from datetime import datetime

from flask import Blueprint
from flask_restx import Api, Resource, fields, reqparse
from sqlalchemy import case, func

from models import TestResult, db

blueprint = Blueprint("api", __name__)

api = Api(
    blueprint,
    version="1.0",
    title="TestResult API",
    description="A simple TestResult API",
)

ns = api.namespace("test_results", description="Test results")

test_result = api.model(
    "TestResult",
    {
        "id": fields.Integer(
            readonly=True, description="The test result unique identifier"
        ),
        "device_type": fields.String(required=True, description="The device type"),
        "operator": fields.String(required=True, description="The operator"),
        "time": fields.DateTime(required=True, description="The time of testing"),
        "success": fields.Integer(required=True, description="The success of testing", min=0, max=1),
    },
)

ns_stats = api.namespace("stats", description="Stats")

stats = api.model(
    "stats",
    {
        "device_type": fields.String(required=True, description="The device type"),
        "overall_tests": fields.Integer(
            required=True, description="The overall number of tests"
        ),
        "successful_tests": fields.Integer(
            required=True, description="The number of successful tests"
        ),
        "failed_tests": fields.Integer(
            required=True, description="The number of failed tests"
        ),
    },
)

stats_parser = reqparse.RequestParser()
stats_parser.add_argument("operator", type=str, help="Operator name")


@ns.route("/")
class TestResultList(Resource):
    """Shows a list of all test results, and lets you POST to add new tasks"""

    @ns.doc("list_test_results")
    @ns.marshal_list_with(test_result)
    def get(self):
        """List all test results"""
        results = TestResult.query.all()
        return results

    @ns.doc("create_result")
    @ns.expect(test_result)
    @ns.marshal_with(test_result, code=201)
    @ns.response(422, "Invalid format of time field.")
    def post(self):
        """Create a new test result"""
        try:
            result_time = datetime.strptime(ns.payload.pop("time"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {}, 422
        result = TestResult(**ns.payload, time=result_time)
        db.session.add(result)
        db.session.commit()
        return result, 201


@ns.route("/<int:id>")
@ns.response(404, "Test result not found")
@ns.param("id", "The test result unique identifier")
class TestResultSingle(Resource):
    """Show a single test result item and lets you delete them"""

    @ns.doc("get_test_result")
    @ns.marshal_with(test_result)
    def get(self, id):
        """Fetch a given resource"""
        result = TestResult.query.get(id)
        return result

    @ns.doc("delete_test_result")
    @ns.response(204, "Test result deleted")
    def delete(self, id):
        """Delete a test result given its identifier"""
        result = TestResult.query.get(id)
        db.session.delete(result)
        db.session.commit()
        return {}, 204


@ns_stats.route("/")
class StatsList(Resource):
    """Shows a list of all test results, and lets you POST to add new tasks"""

    @ns_stats.doc("list_stats")
    @ns_stats.marshal_list_with(stats)
    @ns_stats.expect(stats_parser)
    def get(self):
        """List all stats"""
        results = db.session.query(
            TestResult.device_type,
            func.count(TestResult.id).label("overall_tests"),
            func.sum(TestResult.success).label("successful_tests"),
            func.count(case((TestResult.success < 1, TestResult.id), else_=None)).label(
                "failed_tests"
            ),
        ).group_by(TestResult.device_type)
        args = stats_parser.parse_args()
        operator = getattr(args, "operator")
        if operator:
            results = results.filter(TestResult.operator == operator)

        return results.all()
