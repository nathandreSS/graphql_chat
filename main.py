from ariadne.asgi import GraphQL
from ariadne.objects import MutationType, QueryType
from ariadne import (load_schema_from_path, make_executable_schema, snake_case_fallback_resolvers)
from ariadne.constants import PLAYGROUND_HTML
from flask import request, jsonify
from api import app, db
from api import models
from api.queries import query
from api.mutations import mutation
from api.subscriptions import subscription


type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(
    type_defs, query, mutation, subscription, snake_case_fallback_resolvers
)

graphql_app = GraphQL(schema, debug=True)

@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()

    success, result = GraphQL(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code