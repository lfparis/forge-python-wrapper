from forge import ForgeApp  # noqa:E402


def main():

    app = ForgeApp(hub_id="<BIM 360 Hub ID>", three_legged=True)
    app.get_projects()
    pj = app.find_project("<Project Name>")

    file_name = "<filename.extension>"
    item = pj.find(file_name)
    item.publish()


if __name__ == "__main__":
    main()
