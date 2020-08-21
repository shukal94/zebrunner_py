import datetime
import logging
import time
import pytest
import uuid

from zebrunnerpy.resources import test_result_v1
from .resource_constants import TestStatus


class BaseZafiraListener:

    def __init__(self, state):
        self.state = state

        self.initialized = self.initialize_zafira()

    def initialize_zafira(self):
        enabled = False
        try:
            if self.state.is_enabled:

                self.state.is_enabled = self.state.zc.is_zafira_available()

                if self.state.is_enabled:
                    self.state.refresh_token = self.state.zc.refresh_token(self.state.access_token).json()
                    self.state.zc.auth_token = self.state.refresh_token['authToken']
                    logging.info("Zafira is " + "available" if self.state.is_enabled else "unavailable")

            enabled = self.state.is_enabled
        except Exception as e:
            logging.error("Unable to initialize connector: {}".format(e))
        return enabled

    def compose_package_name(self, path_entries_list):
        if len(path_entries_list) == 2:
            return path_entries_list[0]
        return path_entries_list[0] + '/' + self.compose_package_name(path_entries_list[1:])

    def add_artifact_to_test(self, test, artifact_name, artifact_link, expires_in=None):
        """
        Adds test artifact to test
        """
        try:
            self.state.zc.add_test_artifact_to_test(test["id"], artifact_link, artifact_name, expires_in)
        except Exception as e:
            logging.error("Unable to add artifact to test correctly: {}".format(e))

    def on_test_success(self):
        """
        An abstract handler for posting successfull test onto Zafira UI
        """

    def on_test_failure(self, message):
        """
        An abstract handler for posting failed test onto Zafira UI
        :param message: error message from failing test
        """

    def on_test_skipped(self, message):
        """
        An abstract handler for posting skipped test onto Zafira UI
        :param message: skip reason
        """

    def add_work_item_to_test(self, test_id, work_item):
        if not self.state.is_enabled:
            return
        try:
            work_items = list()
            work_items.append(work_item if len(work_item) < self.state.MAX_LENGTH_OF_WORKITEM else 'Skipped')
            self.state.zc.create_test_work_items(test_id, work_items)
        except Exception as e:
            logging.error("Unable to add work item: {}".format(e))


class PyTestZafiraListener(BaseZafiraListener):
    """
    Contains hook implementations
    """

    FRAMEWORK = 'pytest'

    def __init__(self, state):
        super().__init__(state)

    @pytest.hookimpl
    def pytest_sessionstart(self, session):
        """
        Setup-class handler, signs in user, creates a testsuite,
        testcase, job and registers testrun in Zafira
        """
        if not self.initialized:
            return
        try:
            self.state.test_run = self.state.zc.start_test_run(
                session.name,
                datetime.datetime.utcnow(),
                self.FRAMEWORK,
                self.state.zafira_project
            )
            self.state.test_run_id = self.state.test_run.json()["id"]
        except Exception as e:
            self.state.is_enabled = False
            logging.error("Undefined error during test run registration! {}".format(e))

    @pytest.hookimpl
    def pytest_runtest_setup(self, item):
        """
        Setup handler, set up initial parameters for test,
        attaches to testsuite, registers and starts the test
        """
        if not self.state.is_enabled:
            return
        try:
            test_name = item.name
            class_name = item.nodeid.split('::')[1]
            uid = str(uuid.uuid4())
            self.state.test = self.state.zc.start_test(
                uid,
                self.state.test_run_id,
                test_name,
                datetime.datetime.utcnow(),
                class_name
            )
            self.state.test_id = self.state.test.json()["id"]
        except Exception as e:
            logging.error("Undefined error during test case/method start! {}".format(e))

    @pytest.hookimpl
    def pytest_runtest_teardown(self, item):
        """
        Teardown handler. Finishes test, adds workitems if needed
        """
        if not self.state.is_enabled:
            return
        try:

            self.state.zc.finish_test(self.state.test_run_id, self.state.test_id, self.state.test.json())
        except Exception as e:
            logging.error("Unable to finish test run correctly: {}".format(e))

    @pytest.hookimpl
    def pytest_runtest_logreport(self, report):
        """
        Set test status, stacktrace if needed
        :param report: info about test
        """
        if not self.state.is_enabled:
            return
        try:
            if report.when == 'setup':
                if report.failed:
                    self.on_test_failure(report)
            if report.when == 'call':
                test_result = report.outcome
                if test_result is 'passed':
                    self.on_test_success()
                if test_result is 'failed':
                    self.on_test_failure(report)

        except Exception as e:
            logging.error("Unable to finish test correctly: {}".format(e))

    @pytest.hookimpl
    def pytest_sessionfinish(self, session, exitstatus):
        """
        Teardown-class handler, closes the testrun
        """
        if not self.state.is_enabled:
            return
        try:
            self.state.zc.finish_test_run(self.state.test_run["id"])
        except Exception as e:
            logging.error("Unable to finish test run correctly: {}".format(e))

    def on_test_success(self):
        test_result_v1["result"] = 'passed'

    def on_test_failure(self, message):
        test_result_v1["result"] = 'failed'
        test_result_v1["reason"] = message.longreprtext

    def on_test_skipped(self, message):
        self.state.test['message'] = message.longreprtext
        if not hasattr(message, 'wasxfail'):
            self.state.test['status'] = TestStatus.SKIPPED.value
        else:
            self.state.test['status'] = TestStatus.FAILED.value
