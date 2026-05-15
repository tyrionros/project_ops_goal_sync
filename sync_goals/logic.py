import difflib
from . import api
from . import config

def get_closest_match(name, possibilities):
    if not possibilities:
        return None
    matches = difflib.get_close_matches(name, possibilities, n=1, cutoff=0.0)
    return matches[0] if matches else None

def sync_project_goals(token, project):
    project_name = project.get("msdyn_subject", "Unnamed Project")
    project_id = project["msdyn_projectid"]
    print(f"\nProcessing project: {project_name}")
    
    op_set_id = None
    try:
        existing_goals = api.fetch_existing_goals(token, project_id)
        print(f"  Project has {len(existing_goals)} existing goals.")
        
        op_set_id = api.create_operation_set(token, project_id)
        all_queued = True
        
        assigned_targets = set()
        unprocessed_existing = []
        
        # Step 1: Handle Explicit Mappings
        for goal in existing_goals:
            old_name = goal["msdyn_name"]
            if old_name in config.GOAL_MAPPING:
                target_name = config.GOAL_MAPPING[old_name]
                if api.update_goal_in_operation_set(token, op_set_id, goal["msdyn_projectgoalid"], target_name):
                    print(f"    [MAPPED UPDATE] '{old_name}' -> '{target_name}'")
                    assigned_targets.add(target_name)
                else:
                    all_queued = False
            else:
                unprocessed_existing.append(goal)
        
        # Step 2: Handle Remaining Existing Goals with Fuzzy Matching
        remaining_targets = [t for t in config.GOALS_TO_ADD if t not in assigned_targets]
        
        for goal in unprocessed_existing:
            old_name = goal["msdyn_name"]
            if remaining_targets:
                closest_target = get_closest_match(old_name, remaining_targets)
                if api.update_goal_in_operation_set(token, op_set_id, goal["msdyn_projectgoalid"], closest_target):
                    print(f"    [FUZZY UPDATE] '{old_name}' -> '{closest_target}'")
                    assigned_targets.add(closest_target)
                    remaining_targets.remove(closest_target)
                else:
                    all_queued = False
            else:
                # No more target slots, delete extra
                if api.delete_goal_from_operation_set(token, op_set_id, goal["msdyn_projectgoalid"], old_name):
                    print(f"    [DELETE QUEUED] '{old_name}' (Exceeds target list)")
                else:
                    all_queued = False
        
        # Step 3: Create missing targets
        final_remaining_targets = [t for t in config.GOALS_TO_ADD if t not in assigned_targets]
        for target_name in final_remaining_targets:
            if api.create_goal_in_operation_set(token, op_set_id, project_id, target_name):
                print(f"    [CREATE QUEUED] '{target_name}'")
            else:
                all_queued = False
        
        if all_queued:
            print("  Executing synchronization batch...")
            api.execute_operation_set(token, op_set_id)
            print("  [SUCCESS] Synchronization triggered.")
        else:
            print("  [ERROR] Some operations failed to queue. Abandoning batch.")
            api.abandon_operation_set(token, op_set_id)
            
    except Exception as e:
        print(f"  [ERROR] Failed project {project_name}: {e}")
        if op_set_id:
            api.abandon_operation_set(token, op_set_id)
