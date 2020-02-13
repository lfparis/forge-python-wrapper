# Forge Python Wrapper

Forge API Client Wrapper for Python

## Installing

WIP

## Documentation

WIP

### Usage Examples

```python
"""
If the following Environment Variables are defined there is no need to explicitly provide them when constructing the ForgeApp:
    For 2-legged context:
        FORGE_HUB_ID
        FORGE_CLIENT_ID
        FORGE_CLIENT_SECRET
    Extras for 3-legged context:
        FORGE_REDIRECT_URI
        FORGE_USERNAME
        FORGE_PASSWORD
"""

# 3-legged authorization - Needed to work with BIM 360 Team Hubs
app = ForgeApp(
    client_id="your_app_client_id",
    client_secret="your_app_client_secret",
    three_legged=True,
    redirect_uri="your_app_redirect_uri",
    username="your_autodesk_username",
    password="your_autodesk_password",
)

app.get_hubs()
app.hub_id = app.hubs[0]["id"]

app.get_projects(source="docs")
project = app.find_project("Project Name", key="name")
project = app.find_project("4337130a-0533-4411-ae59-923819163d7a", key="id")

project.get_top_folders()
top_folder = project.top_folder

project.get_project_files_folder()
contents = project.get_folder_contents(pj.project_files_folder["id"])

parent_folder_id = pj.project_files_folder["id"]
project.add_folder(parent_folder_id, "New Folder Name")


# 2-legged authorization - Needed for methods that use the BIM 360 API
app = ForgeApp(
    client_id="your_app_client_id",
    client_secret="your_app_client_secret",
    hub_id="your_hub_id",
)

app.get_companies()
company = app.find_company("Company Name")

app.get_users()
admin_user = app.find_user("admin_user@domain.com")
normal_user_1 = app.find_user("other_user_1@domain.com")
normal_user_2 = app.find_user("other_user_2@domain.com")

app.get_projects(source="all")

new_project = app.add_project("New Project Name")

new_project.update(name="Updated Project Name", status="active")

new_project.get_project_roles
roles = new_project.roles
role_id = roles[0]["id"]

new_project.x_user_id = admin_user["uid"]
new_project.add_users([admin_user], access_level="admin")
new_project.add_users([normal_user_1, normal_user_2], access_level="user", role_id=role_id)

new_role_id = roles[1]["id"]
new_project.update_user(normal_user_1, company_id=company["id"], role_id=new_role_id)
```

## License
[MIT](https://opensource.org/licenses/MIT)