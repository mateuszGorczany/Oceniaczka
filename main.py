from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session  # https://pythonhosted.org/Flask-Session
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler
from auth import _load_cache, _get_token_from_cache, \
      _build_auth_code_flow,_build_msal_app, _save_cache
import msal
import requests
import services as svcs
from logging import StreamHandler
from opencensus.ext.azure.log_exporter import AzureLogHandler
import app_config
import multiprocessing_logging
from azure.cosmos import CosmosClient

multiprocessing_logging.install_mp_handler()

def db_client():
    client = CosmosClient(app_config.DB_ACCOUNT_URI, app_config.DB_ACCOUNT_KEY)
    database = client.get_database_client(app_config.DB_NAME)
    container = database.get_container_client("Applicants")
    return container

class Services:

    def __init__(self) -> None:
        self.db_client = db_client()
        self.user_service = svcs.UserSerivce()
        self.voting_service = svcs.VotingService()
        self.applicants_service = svcs.ApplicantsService(db_client)

def set_up_app():
    app = Flask(__name__)
    app.config.from_object(app_config)
    Session(app)
    middleware = FlaskMiddleware(
        app,
        exporter=AzureExporter(connection_string=app_config.APPLICATIONINSIGHTS_CONNECTION_STRING),
        sampler=ProbabilitySampler(rate=1.0),
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    return app, middleware


app, middleware = set_up_app()
handler = AzureLogHandler(
    connection_string=app_config.APPLICATIONINSIGHTS_CONNECTION_STRING,
)
streamHandler = StreamHandler(handler)
app.logger.addHandler(streamHandler)
# app.logger.addHandler(handler)
services = Services()

@app.route("/")
def index():
    # if not session.get("user"):
    # if not services.user_service.is_user_logged_in():
    #     return redirect(url_for("login"))
    services.user_service.load_current_user()
    user = services.user_service.current_user
    return render_template(
        "index.html", 
        user=user, 
        applicants=services.applicants_service.list_applicants(),
        version=msal.__version__
    )


@app.route("/login")
def login():
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    services.user_service.load_current_user()
    return redirect(session["flow"]["auth_uri"])


@app.route(
    app_config.REDIRECT_PATH
)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args
        )
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    services.user_service.current_user = None
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY
        + "/oauth2/v2.0/logout"
        + "?post_logout_redirect_uri="
        + url_for("index", _external=True)
    )


@app.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={"Authorization": "Bearer " + token["access_token"]},
    ).json()
    return render_template("display.html", result=graph_data)

@app.route("/vote/<applicant_id>")
def vote(applicant_id):
    services.user_service.load_current_user()
    current_uer_id = services.user_service.current_user.ID
    if request.args.get("vote_type") == "yes":
        services.voting_service.vote_yes(applicant_id, current_uer_id)
    if request.args.get("vote_type") == "no":
        services.voting_service.vote_no(applicant_id, current_uer_id)
    
    return jsonify(success=True)

app.jinja_env.globals.update(
    _build_auth_code_flow=_build_auth_code_flow
)  # Used in template

if __name__ == "__main__":
    app.run(debug=True)
