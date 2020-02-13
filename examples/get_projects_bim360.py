from forge import ForgeApp


def main():

    app = ForgeApp()
    hub_type = ForgeApp.TYPES[ForgeApp.BIM_360_TYPES["b."]]["hubs"]

    app.get_hubs()
    hub_id = [
        hub["id"]
        for hub in app.hubs
        if hub["attributes"]["extension"]["type"] == hub_type
    ][0]
    app.hub_id = hub_id

    app.get_projects(source="all")

    for project in app.projects:
        print(project.name)
        print(project.data)


if __name__ == "__main__":
    main()
