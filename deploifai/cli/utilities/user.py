def parse_user_profiles(me_user_query):
    personal_workspace = me_user_query["account"]
    team_workspaces = list(map(lambda x: x["account"], me_user_query["teams"]))
    return personal_workspace, team_workspaces
