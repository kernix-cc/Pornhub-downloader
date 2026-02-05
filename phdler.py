#!/usr/bin/env python
from functions import *
from resume_manager import check_playlist_completion, resume_download, show_download_status, extract_type_and_name_from_url

def main():

    check_for_database()

    if len(sys.argv) > 1:

        if sys.argv[1] == "start":
            dl_start()
            
        elif sys.argv[1] == "custom":
            if len(sys.argv) > 2:
                custom_dl(sys.argv[2])
            else:
                how_to_use("Missing item")

        elif sys.argv[1] == "add":
            if len(sys.argv) > 2:
                add_check(sys.argv[2])
            else:
                how_to_use("Missing item")

        elif sys.argv[1] == "delete":
            if len(sys.argv) > 2:
                type_check(sys.argv[2])
                list_items(sys.argv[2])
                u_input = input("Please enter the ID to delete (or c to cancel): ")
                if u_input == "c":
                    print("Operation canceled.")
                else:
                    delete_item(u_input)
            else:
                how_to_use("Missing item")

        elif sys.argv[1] == "list":
            if len(sys.argv) > 2:
                type_check(sys.argv[2])
                list_items(sys.argv[2])
            else:
                how_to_use("Missing item")

        elif sys.argv[1] == "resume":
            if len(sys.argv) > 2:
                url = sys.argv[2]
                
                # Try to extract type and name from URL if not provided
                if len(sys.argv) > 4:
                    item_type = sys.argv[3]
                    item_name = sys.argv[4]
                else:
                    # Auto-extract from URL
                    item_type, item_name = extract_type_and_name_from_url(url)
                    if item_type is None:
                        how_to_use("Could not parse URL. Please provide type and name explicitly.")
                        sys.exit()
                
                try:
                    dl_location = get_dl_location('DownloadLocation')
                    dl_location = os.path.normpath(dl_location)
                except:
                    dl_location = os.path.normpath('./model')
                resume_download(url, item_type, item_name, dl_location)
            else:
                how_to_use("Missing URL for resume command")

        elif sys.argv[1] == "check":
            if len(sys.argv) > 2:
                url = sys.argv[2]
                
                # Try to extract type and name from URL if not provided
                if len(sys.argv) > 4:
                    item_type = sys.argv[3]
                    item_name = sys.argv[4]
                else:
                    # Auto-extract from URL
                    item_type, item_name = extract_type_and_name_from_url(url)
                    if item_type is None:
                        how_to_use("Could not parse URL. Please provide type and name explicitly.")
                        sys.exit()
                
                try:
                    dl_location = get_dl_location('DownloadLocation')
                    dl_location = os.path.normpath(dl_location)
                except:
                    dl_location = os.path.normpath('./model')
                download_dir = os.path.join(dl_location, item_name)
                check_playlist_completion(download_dir, url, item_type, item_name)
            else:
                how_to_use("Missing URL for check command")

        elif sys.argv[1] == "status":
            if len(sys.argv) > 2:
                download_dir = sys.argv[2]
                show_download_status(download_dir)
            else:
                how_to_use("Missing arguments for status command")

        elif sys.argv[1] == "help":
            help_command()

        else:
            how_to_use("Command not found!")

    else:
        how_to_use("Missing command.")


if __name__ == '__main__':
    main()
