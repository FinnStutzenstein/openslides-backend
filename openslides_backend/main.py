import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Any

from gunicorn.app.base import BaseApplication

from .shared.interfaces import LoggingModule, WSGIApplication

# ATTENTION: We use the Python builtin logging module. To change this use
# something like "import custom_logging as logging".

DEFAULT_ADDRESSES = {
    "ActionView": "0.0.0.0:9002",
    "PresenterView": "0.0.0.0:9003",
}


class OpenSlidesBackendGunicornApplication(BaseApplication):  # pragma: no cover
    """
    Standalone application class for Gunicorn. It prepares Gunicorn for using
    OpenSlidesBackendWSGIApplication via OpenSlidesBackendWSGIContainer either
    with action component or with presenter component.
    """

    def __init__(self, view_name: str, *args: Any, **kwargs: Any) -> None:
        # Setup global loglevel.
        if os.environ.get("OPENSLIDES_BACKEND_DEBUG"):
            logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        self.view_name = view_name
        if self.view_name not in ("ActionView", "PresenterView"):
            raise ValueError(
                f"View name has to be ActionView or PresenterView, not {self.view_name}."
            )
        logger.debug(f"Create gunicorn application for {self.view_name}.")
        super().__init__(*args, **kwargs)

    def load_config(self) -> None:
        loglevel = "debug" if os.environ.get("OPENSLIDES_BACKEND_DEBUG") else "info"
        options = {
            "bind": DEFAULT_ADDRESSES[self.view_name],
            "worker_tmp_dir": "/dev/shm",  # See https://pythonspeed.com/articles/gunicorn-in-docker/
            "timeout": int(os.environ.get("OPENSLIDES_BACKEND_WORKER_TIMEOUT", "30")),
            "loglevel": loglevel,
            "reload": loglevel == "debug",
            "reload_engine": "auto",  # This is the default however.
        }
        for key, value in options.items():
            self.cfg.set(key, value)

    def load(self) -> WSGIApplication:
        # We import this here so Gunicorn can use its reload feature properly.
        from .wsgi import create_wsgi_application
        from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware

        # TODO: Fix this typing problem.
        logging_module: LoggingModule = logging  # type: ignore
        return OpenTelemetryMiddleware(create_wsgi_application(logging_module, self.view_name))


def start_action_server() -> None:  # pragma: no cover
    setup_opentelemetry()
    OpenSlidesBackendGunicornApplication(view_name="ActionView").run()


def start_presenter_server() -> None:  # pragma: no cover
    setup_opentelemetry()
    OpenSlidesBackendGunicornApplication(view_name="PresenterView").run()


def start_addendum_server() -> None:  # pragma: no cover
    # TODO: Start a permanent running process that listens to event stream and
    # pushes additional fqfields that might be new for some users.
    print("Start addendum server ...")
    while True:
        time.sleep(1000000000)


def start_them_all() -> None:  # pragma: no cover
    print(
        f"Start all components in child processes. Parent process id is {os.getpid()}."
    )
    processes = {
        "action": multiprocessing.Process(target=start_action_server),
        "presenter": multiprocessing.Process(target=start_presenter_server),
        # "addendum": multiprocessing.Process(target=start_addendum_server),
    }
    for process in processes.values():
        process.start()

    def sigterm_handler(signalnum: int, current_stack_frame: Any) -> None:
        strsignal = signal.strsignal  # type: ignore
        print(
            f"Parent process {os.getpid()} received {strsignal(signalnum)} "
            "signal. Terminate all child processes first."
        )
        for child in multiprocessing.active_children():
            child.terminate()
            child.join()
        print(f"Parent process {os.getpid()} terminated successfully.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    while True:
        for name, process in processes.items():
            if not process.is_alive():
                process.join()
                print(
                    f"Component {name} terminated. Terminate all other components now."
                )
                for other_name, other_process in processes.items():
                    if name != other_name:
                        other_process.terminate()
                        other_process.join()
                print("Parent process terminated.")
                sys.exit(1)
        time.sleep(0.1)

def setup_opentelemetry():
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchExportSpanProcessor, SimpleExportSpanProcessor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter

    docker_id = "todo"  # os.environ.get("DOCKER_ID")  # TODO: env service
    resource = Resource.create({
        "service.name": "backend",
        "service.instance.id": docker_id
    })
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    span_exporter = OTLPSpanExporter(endpoint="otel-collector:55680")
    #span_exporter = ConsoleSpanExporter()
    # BatchExportSpanProcessor does not work currently
    span_processor = SimpleExportSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)

    RequestsInstrumentor().instrument()

def main() -> None:  # pragma: no cover
    component = os.environ.get("OPENSLIDES_BACKEND_COMPONENT", "all")
    if component == "action":
        start_action_server()
    elif component == "presenter":
        start_presenter_server()
    elif component == "addendum":
        start_addendum_server()
    elif component == "all":
        start_them_all()
    else:
        print(
            f"Error: OPENSLIDES_BACKEND_COMPONENT must not be {component}.",
            file=sys.stderr,
        )
        sys.stderr.flush()
        sys.exit(1)
    sys.exit(0)
