import sys
import os
import time

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)

from forge import ForgeApp  # noqa:E402
from forge.utils import pretty_print  # noqa:F401


def main():

    # STEP 1 - Get original file
    app_old_hub = ForgeApp(
        hub_id=os.environ.get("FORGE_HUB_ID_OLD"), three_legged=True
    )

    app_old_hub.get_projects()

    pj = app_old_hub.find_project("EMEA BIR 55 Colmore Row")

    pj.get_top_folders()
    pj.get_contents()
    for folder in pj.top_folders:
        print(folder.contents)

    # pj = app_old_hub.find_project("EMEA LON 1 Poultry")

    # pj.get_top_folders()
    # print(pj.project_files)

    # parent_folder_id = pj.top_folders[0]["id"]
    # parent_contents = pj.get_folder_contents(parent_folder_id)

    # # TODO - Add Method  - Walk Project Folder Structure
    # for item in parent_contents:
    #     print("Name: {}".format(item["id"]))
    #     print("Id: {}".format(item["type"]))
    #     print("Type: {}".format(item["attributes"]["displayName"]))
    #     print("Hidden: {}".format(item["attributes"]["hidden"]))
    #     print("\n")

    # file_name = "Birmingham-55ColmoreRow-Project1-ExistingConditions_OLD.rvt"

    # item_id = [
    #     item
    #     for item in parent_contents
    #     if item["attributes"]["displayName"] == file_name
    # ][0]["id"]

    # item = app_old_hub.api.dm.get_item(pj.id["dm"], item_id)
    # # pretty_print(item)

    # storage_id = item["included"][0]["relationships"]["storage"]["data"]["id"]
    # bucket_key, object_name = storage_id.split(":")[-1].split("/")

    # app_old_hub.logger.info("Downloading File {}".format(file_name))
    # obj_bytes = app_old_hub.api.dm.get_object(bucket_key, object_name)
    # app_old_hub.logger.info(
    #     "Download done - file size: {}".format(len(obj_bytes))
    # )

    # # filepath = "/Users/lparis2/repos/forge-python-wrapper/test.rvt"
    # # with open(filepath, "wb") as fp:
    # #     fp.write(obj_bytes)

    # # STEP 2 - Get original file
    # app_new_hub = ForgeApp(three_legged=True)

    # app_new_hub.get_projects()

    # pj = app_new_hub.find_project("FPW TEST 4")

    # pj.get_top_folders()
    # print(pj.project_files)
    # print(pj.plans)

    # pj = app_new_hub.find_project("EU GB LON The Hewett")

    # pj.get_top_folders()
    # print(pj.project_files)
    # print(pj.plans)

    # for folder in pj.top_folders:
    #     print(folder.name)
    #     print(folder.id)
    #     pretty_print(folder.data)
    #     print(folder.project.name)

    # parent_folder_id = pj.project_files_folder["id"]

    # # add storage
    # storage = app_new_hub.api.dm.post_storage(
    #     pj.id["dm"], "folders", parent_folder_id, file_name
    # )

    # storage_id = storage["data"]["id"]
    # bucket_key, object_name = storage_id.split(":")[-1].split("/")

    # # filepath = "/Users/lparis2/repos/forge-python-wrapper/test.rvt"
    # # with open(filepath, "rb") as fp:
    # #     obj_bytes = fp.read()

    # # upload object
    # data = app_new_hub.api.dm.put_object(bucket_key, object_name, obj_bytes)
    # pretty_print(data)

    # file_name = "ASDAS.rvt"

    # # add item
    # data = app_new_hub.api.dm.post_item(
    #     pj.id["dm"], parent_folder_id, storage_id, file_name,
    # )
    # pretty_print(data)
    # item_id = data["data"]["id"]

    # print("I'm only sleeping")
    # time.sleep(15)

    # file_name = "AGATA.rvt"

    # # add storage
    # storage = app_new_hub.api.dm.post_storage(
    #     pj.id["dm"], "folders", parent_folder_id, file_name
    # )

    # storage_id = storage["data"]["id"]
    # bucket_key, object_name = storage_id.split(":")[-1].split("/")

    # data = app_new_hub.api.dm.put_object(bucket_key, object_name, obj_bytes)

    # # add version
    # data = app_new_hub.api.dm.post_item_version(
    #     pj.id["dm"], storage_id, item_id, file_name,
    # )
    # pretty_print(data)


if __name__ == "__main__":
    main()
