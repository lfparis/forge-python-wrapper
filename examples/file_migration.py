from forge import ForgeApp  # noqa:E402


def main():

    # STEP 1 - Download from Old Hub
    app_hub_1 = ForgeApp(hub_id="<BIM 360 Team Hub ID>", three_legged=True)
    app_hub_1.get_projects()
    pj = app_hub_1.find_project("<Project Name>")

    file_name = "<A File Name.extension>"
    item = pj.find(file_name)
    item.download()

    # STEP 2 - Upload to New Hub
    app_hub_2 = ForgeApp(hub_id="<BIM 360 Doc Hub ID>", three_legged=True)
    app_hub_2.get_projects()
    pj = app_hub_2.find_project("<New Project Name>")
    pj.get_top_folders()

    pj.project_files.add_item(file_name, item.bytes)


if __name__ == "__main__":
    main()
