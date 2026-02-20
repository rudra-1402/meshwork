# MeshWork — Fix Test Warnings (SQLAlchemy Deprecations)                                                                                         
        2 +                                                                                                                                                 
        3 +## Context                                                                                                                                       
        4 +The 51-test suite passes cleanly but produces 67 warnings in two categories:                                                                     
        5 +1. `DeprecationWarning: datetime.datetime.utcnow()` — SQLAlchemy triggers this because model column defaults pass `datetime.utcnow` as a         
          +callable. Python 3.12+ deprecates `utcnow()`.                                                                                                    
        6 +2. `LegacyAPIWarning: Query.get()` — SQLAlchemy 2.0 deprecated `Model.query.get(id)` in favour of `db.session.get(Model, id)`. Triggered         
          +at runtime for every code path exercised by tests.                                                                                               
        7 +                                                                                                                                                 
        8 +The goal: zero warnings on `pytest tests/ -v`.                                                                                                   
        9 +                                                                                                                                                 
       10 +---                                                                                                                                              
       11 +                                                                                                                                                 
       12 +## Fix 1 — `datetime.utcnow` → `datetime.now(timezone.utc)`                                                                                      
       13 +                                                                                                                                                 
       14 +### Pattern                                                                                                                                      
       15 +| Before | After |                                                                                                                               
       16 +|--------|-------|                                                                                                                               
       17 +| `default=datetime.utcnow` | `default=lambda: datetime.now(timezone.utc)` |                                                                     
       18 +| `onupdate=datetime.utcnow` | `onupdate=lambda: datetime.now(timezone.utc)` |                                                                   
       19 +| `datetime.utcnow()` (in service code) | `datetime.now(timezone.utc)` |                                                                         
       20 +                                                                                                                                                 
       21 +Each file also needs `from datetime import timezone` added to its imports.                                                                       
       22 +                                                                                                                                                 
       23 +### Files (20 total)                                                                                                                             
       24 +**Models:**                                                                                                                                      
       25 +- `app/models/project.py`                                                                                                                        
       26 +- `app/models/project_member.py`                                                                                                                 
       27 +- `app/models/project_language.py`                                                                                                               
       28 +- `app/models/user.py`                                                                                                                           
       29 +- `app/models/event_models.py`                                                                                                                   
       30 +- `app/models/language.py`                                                                                                                       
       31 +- `app/models/whitelisted_email.py`                                                                                                              
       32 +- `app/models/college_personnel.py`                                                                                                              
       33 +- `app/models/xp_transaction.py`                                                                                                                 
       34 +- `app/models/user_skill.py`                                                                                                                     
       35 +- `app/models/community_message.py`                                                                                                              
       36 +- `app/models/community_task.py`                                                                                                                 
       37 +- `app/models/community_file.py`                                                                                                                 
       38 +- `app/models/community_poll.py`                                                                                                                 
       39 +- `app/models/task_completion.py`                                                                                                                
       40 +- `app/models/community_moderator.py`                                                                                                            
       41 +- `app/models/community.py`                                                                                                                      
       42 +- `app/models/community_member.py`                                                                                                               
       43 +                                                                                                                                                 
       44 +**Services (use `datetime.utcnow()` in logic):**                                                                                                 
       45 +- `app/services/college_personnel_services.py`                                                                                                   
       46 +- `app/services/skill_service.py`                                                                                                                
       47 +                                                                                                                                                 
       48 +---                                                                                                                                              
       49 +                                                                                                                                                 
       50 +## Fix 2 — `Query.get()` → `db.session.get()`                                                                                                    
       51 +                                                                                                                                                 
       52 +### Pattern                                                                                                                                      
       53 +```python                                                                                                                                        
       54 +# Before                                                                                                                                         
       55 +Model.query.get(some_id)                                                                                                                         
       56 +                                                                                                                                                 
       57 +# After                                                                                                                                          
       58 +db.session.get(Model, some_id)                                                                                                                   
       59 +```                                                                                                                                              
       60 +`db` is already imported as `from app.extensions import db` in all these files.                                                                  
       61 +                                                                                                                                                 
       62 +### Files (grouped by type)                                                                                                                      
       63 +**Routes (hit by current tests — highest priority):**                                                                                            
       64 +- `app/routes/project_routes.py` — line 149                                                                                                      
       65 +- `app/routes/dashboard_routes.py` — lines 22, 57, 95                                                                                            
       66 +- `app/routes/profile_routes.py` — lines 29, 72, 111, 159, 182, 213, 238                                                                         
       67 +- `app/routes/community_routes.py` — lines 119, 158, 194, 259                                                                                    
       68 +- `app/routes/admin_routes.py` — lines 32, 42, 77, 145, 208, 260, 346                                                                            
       69 +- `app/routes/leaderboard_routes.py` — line 161                                                                                                  
       70 +- `app/routes/scoring_routes.py` — line 341                                                                                                      
       71 +                                                                                                                                                 
       72 +**Services:**                                                                                                                                    
       73 +- `app/services/project_service.py` — lines 74, 388, 710                                                                                         
       74 +- `app/services/college_personnel_services.py` — lines 30, 116, 150, 187, 230, 260, 292                                                          
       75 +- `app/services/community_service.py` — lines 93, 146, 201, 224, 346, 381                                                                        
       76 +- `app/services/email_validation_service.py` — line 188                                                                                          
       77 +- `app/services/college_auth_services.py` — line 29                                                                                              
       78 +- `app/services/auth_services.py` — line 29                                                                                                      
       79 +- `app/services/whitelist_service.py` — lines 36, 167                                                                                            
       80 +- `app/services/scoring_service.py` — line 517                                                                                                   
       81 +                                                                                                                                                 
       82 +**Utils:**                                                                                                                                       
       83 +- `app/utils/gamification_helpers.py` — lines 35, 84, 300                                                                                        
       84 +                                                                                                                                                 
       85 +---                                                                                                                                              
       86 +                                                                                                                                                 
       87 +## Execution Order                                                                                                                               
       88 +1. Fix all model files (datetime) — most impactful, causes the bulk of warnings                                                                  
       89 +2. Fix service files (datetime + Query.get)                                                                                                      
       90 +3. Fix route files (Query.get)                                                                                                                   
       91 +4. Fix utils (Query.get)                                                                                                                         
       92 +5. Run `pytest tests/ -v` — expect 51 passed, 0 warnings                                                                                         
       93 +                                                                                                                                                 
       94 +---                                                                                                                                              
       95 +                                                                                                                                                 
       96 +## Verification                                                                                                                                  
       97 +```bash                                                                                                                                          
       98 +cd backend                                                                                                                                       
       99 +python -m pytest tests/ -v 2>&1 | grep -E "warning|passed|failed"                                                                                
      100 +```                                                                                                                                              
      101 +Expected: `51 passed` with no `DeprecationWarning` or `LegacyAPIWarning` lines.    