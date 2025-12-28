import importlib, traceback
routers = [
    'app.routers.version_history',
    'app.routers.quality_metrics',
    'app.routers.constitutional',
    'app.routers.time_tracking',
    'app.routers.gi_formula',
    'app.routers.ck_theory',
    'app.routers.uncertainty',
    'app.routers.governance',
    'app.routers.auth',
    'app.routers.project_context',
    'app.routers.projects',
    'app.routers.modules',
    'app.routers.tasks',
    'app.routers.obsidian',
    'app.routers.kanban_tasks',
    'app.routers.kanban_dependencies',
    'app.routers.kanban_projects',
    'app.routers.kanban_context',
    'app.routers.kanban_ai',
    'app.routers.kanban_archive',
    'app.routers.kanban_websocket',
    'app.routers.test_websocket',
    'app.routers.admin',
    'app.routers.knowledge_feedback',
    'app.routers.knowledge_search',
    'app.routers.websocket_handler',
]
for r in routers:
    try:
        importlib.import_module(r)
        print(r, 'OK')
    except Exception as e:
        print(r, 'FAIL')
        traceback.print_exc()
