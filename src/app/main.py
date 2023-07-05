
from internal.api_client import OncallAPIClient
from internal.utils import ensure_oncall_is_running, load_config


def main():
    """
    App entry point
    """
    app_config = load_config("./configs/app.yaml")

    oncall_server = app_config["oncall_server"]
    ensure_oncall_is_running(oncall_server["host"], int(oncall_server["port"]))

    shedule_config = load_config("./configs/shedule.yaml")
    oncall_client = OncallAPIClient(app_config=app_config, shedule_config=shedule_config)

    oncall_client.process_schedule()


if __name__ == "__main__":
    main()
