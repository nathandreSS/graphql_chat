from ariadne.asgi import GraphQL
from ariadne import (graphql_sync, load_schema_from_path, make_executable_schema, snake_case_fallback_resolvers)
from ariadne.constants import PLAYGROUND_HTML
from flask import request, jsonify

from api import app
from api.queries import query
from api.mutations import mutation
from api.subscriptions import subscription


type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(
    type_defs, query, mutation, subscription, snake_case_fallback_resolvers
)


graphql_app = GraphQL(schema, debug=True)
   

@app.route("/", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200


@app.route("/", methods=["POST"])
def graphql_server():
    data = request.get_json()

    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code
