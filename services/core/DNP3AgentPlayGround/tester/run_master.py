import logging
import sys
import argparse
from dnp3_python.dnp3station.master_new import MyMasterNew
from time import sleep


stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("control_workflow_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)


def input_prompt(display_str=None) -> str:
    if display_str is None:
        display_str = """
======== Your Input Here: ==(master)======
"""
    return input(display_str)


def setup_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:

    # Adding optional argument
    parser.add_argument("-mip", "--master-ip", action="store", default="0.0.0.0", type=str,
                        metavar="<IP>")
    parser.add_argument("-oip", "--outstation-ip", action="store", default="127.0.0.1", type=str,
                        metavar="<IP>")
    parser.add_argument("-p", "--port", action="store", default=20000, type=int,
                        metavar="<PORT>")
    parser.add_argument("-mid", "--master-id", action="store", default=2, type=int,
                        metavar="<ID>")
    parser.add_argument("-oid", "--outstation-id", action="store", default=1, type=int,
                        metavar="<ID>")

    return parser


def print_menu():
    welcome_str = """\
========================= MENU ==================================
<a> - set analog-output point value
<b> - set binary-output point value
<dd> - display database
<dc> - display configuration
=================================================================\
"""
    print(welcome_str)

def main(parser=None, *args, **kwargs):

    if parser is None:
        # Initialize parser
        parser = argparse.ArgumentParser(
            prog="dnp3-master",
            description="Run a dnp3 master",
            # epilog="Thanks for using %(prog)s! :)",
        )
        parser = setup_args(parser)

    # Read arguments from command line
    args = parser.parse_args()

    # dict to store args.Namespace
    d_args = vars(args)
    print(__name__, d_args)

    master_application = MyMasterNew(
        masterstation_ip_str=args.master_ip,
        outstation_ip_str=args.outstation_ip,
        port=args.port,
        masterstation_id_int=args.master_id,
        outstation_id_int=args.outstation_id,

        # channel_log_level=opendnp3.levels.ALL_COMMS,
        # master_log_level=opendnp3.levels.ALL_COMMS
        # soe_handler=SOEHandler(soehandler_log_level=logging.DEBUG)
    )
    _log.info("Communication Config", master_application.get_config())
    master_application.start()
    _log.debug('Initialization complete. Master Station in command loop.')

    sleep(3)
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    count = 0
    while count < 1000:
        # sleep(1)  # Note: hard-coded, master station query every 1 sec.

        count += 1
        print(f"=========== Count {count}")

        if master_application.is_connected:
            # print("Communication Config", master_application.get_config())
            print_menu()
        else:
            print("Communication error.")
            print("Communication Config", master_application.get_config())
            print("Start retry...")
            sleep(2)
            continue

        option = input_prompt()  # Note: one of ["a", "b", "dd", "dc"]
        while True:
            if option == "a":
                print("You chose <a> - set analog-output point value")
                print("Type in <float> and <index>. Separate with space, then hit ENTER.")
                print("Type 'q', 'quit', 'exit' to main menu.")
                input_str = input_prompt()
                if input_str in ["q", "quit", "exit"]:
                    break
                try:
                    p_val = float(input_str.split(" ")[0])
                    index = int(input_str.split(" ")[1])
                    master_application.send_direct_point_command(group=40, variation=4, index=index, val_to_set=p_val)
                    result = master_application.get_db_by_group_variation(group=40, variation=4)
                    print(result)
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "b":
                print("You chose <b> - set binary-output point value")
                print("Type in <[1/0]> and <index>. Separate with space, then hit ENTER.")
                input_str = input_prompt()
                if input_str in ["q", "quit", "exit"]:
                    break
                try:
                    p_val_input = input_str.split(" ")[0]
                    if p_val_input not in ["0", "1"]:
                        raise ValueError("binary-output value only takes '0' or '1'.")
                    else:
                        p_val = True if p_val_input == "1" else False
                    index = int(input_str.split(" ")[1])
                    master_application.send_direct_point_command(group=10, variation=2, index=index, val_to_set=p_val)
                    result = master_application.get_db_by_group_variation(group=10, variation=2)
                    print(result)
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "dd":
                print("You chose < dd > - display database")
                master_application.send_scan_all_request()
                sleep(1)
                db_print = master_application.soe_handler.db
                print(db_print)
                sleep(2)
                break
            elif option == "dc":
                print("You chose < dc > - display configuration")
                print(master_application.get_config())
                sleep(3)
                break
            else:
                print(f"ERROR- your input `{option}` is not one of the following.")
                sleep(1)
                break

    _log.debug('Exiting.')
    master_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
