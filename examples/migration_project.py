from forge import ForgeApp  # noqa:E402


def main():

    # STEP 1 - Get Source Project & Contents from Old Hub
    # Only three-legged authentication works for BIM 360 Teams
    # Therefore, make sure your user has access to the project
    app_hub_1 = ForgeApp(hub_id="<BIM 360 Team Hub ID>", three_legged=True)
    app_hub_1.get_projects()
    source_pj = app_hub_1.find_project("<Project Name>")
    source_pj.include_hidden = True
    source_pj.get_contents()

    # STEP 2 - Get Target Project & Contents from New Hub
    # Use two-legged authentication context, so you can add projects and users
    app_hub_2 = ForgeApp(hub_id="<BIM 360 Doc Hub ID>")
    app_hub_2.get_projects()

    app_hub_2.get_users()
    admin = app_hub_2.find_user("<admin@email.com>")
    target_pj = app_hub_2.find_project(
        "<New Project Name>"
    ) or app_hub_2.add_project("<New Project Name>")
    target_pj.x_user_id = admin["uid"]
    target_pj.add_users([admin], access_level="admin")
    target_pj.get_contents()

    # STEP 3 - Iterate through content and transfer
    for content, level in source_pj.project_files._iter_contents():
        if level == 0:
            target_host = target_pj.project_files
        else:
            target_host = target_pj.find(content.host.name)

        if content.type == "folders":
            target_host.add_sub_folder(content.name)
        elif content.type == "items" and not target_host.find(content.name):
            # Publish latest version
            content.publish()
            # Transfer latest version
            content.transfer(target_host)


if __name__ == "__main__":
    main()
