import os

from .client import client
from .context import Context, Parameter


class ZafiraState:
    """
    Zafira global state representation

    The attributes are:

    .. attribute:: zc
        Zafira API client used for most of activities in listener

    .. attribute:: is_enabled
        Flag, if False - Zafira connector is shutting down

    .. attribute:: service_url
        Zafira web service url

    .. attribute:: access_token
        Long-term access user token generated by Zafira user

    .. attribute:: job_name
        name of CI job where testrun is running

    .. attribute:: artifact_log_name
        name of entry of artifacts

    .. attribute:: artifact_expires_in_default_time
        expiration time of artifact (e.g. screenshot from Amazon)

    .. attribute:: circle_ci_client
        client of CIRCLECI API used for any job info

    .. attribute:: suite_name
        name of test suite

    .. attribute:: job_url
        url of CIRCLECI job

    .. attribute:: user
        user payload for Zafira web service

    .. attribute:: job
        job payload for Zafira web service

    .. attribute:: test_suite
        test suite payload for Zafira web service

    .. attribute:: refresh_token
        used for authentication of user in Zafira

    .. attribute:: test_case
        test case payload for Zafira web service

    .. attribute:: test_run
        test run payload for Zafira web service

    .. attribute:: test
        test payload for Zafira web service

    .. attribute:: ci_test_id
        used for correlation_id in Rabbitmq logging handler, the second part of it

    .. attribute:: ci_run_id
        used for correlation_id in Rabbitmq logging handler, the first part of it

    .. attribute:: skip_reason
        retrieves info from pytest tag, used for log in Zafira UI

    .. attribute:: class_name
        name of test class or feature for grouping by test classes/features in Zafira UI

    .. attribute:: test_name
        name of test used for Zafira UI

    .. attribute:: package
        name of test package grouping by test packages/testruns in Zafira UI

    .. attribute:: MAX_LENGTH_OF_WORKITEM
        maximal length of work item visible on Zafira UI

    .. attribute:: zafira_project
        project filter on Zafira UI

    """

    MAX_LENGTH_OF_WORKITEM = 46

    CONFIG = None

    INSTANCE = None

    def __new__(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = super(ZafiraState, cls).__new__(cls)
        return cls.INSTANCE

    def __init__(self):
        self.zc = client

        self.is_enabled = eval(Context.get(Parameter.ZAFIRA_ENABLED))
        self.service_url = Context.get(Parameter.SERVICE_URL)
        self.access_token = Context.get(Parameter.ACCESS_TOKEN)
        self.zafira_project = Context.get(Parameter.ZAFIRA_PROJECT)

        self.suite_name = str(os.environ.get('JOB_NAME'))
        self.job_url = str(os.environ.get('JOB_URL'))

        self.refresh_token = None

        self.test_run_id = None
        self.test_id = None

        self.user = None
        self.job = None
        self.test_suite = None
        self.test_case = None
        self.test_run = None
        self.test = None

        self.ci_test_id = ''
        self.ci_run_id = ''

        self.skip_reason = None

        self.class_name = None
        self.test_name = None
        self.package = None
