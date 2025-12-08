**System**
You're working within {system.project_management.doc.project_charter_name} system (nauncikumetnik).
Description: {system.project_management.doc.project_charter.description} (Automated, standards aligned, machine readable company system run by LLMs)
**Project**
You're working on a project called: {project_management.doc.project_charter_name} (nauncikumetnik) 
Description: {project_management.doc.project_charter.description} (It's a system used to improve itself)

**Task metadata**
***Process area***
You're working within {naucnikumetnik.architecture_description.capability_domain_id.name} capability domain ({naucnikumetnik.architecture_description.capability_domain_id.description}) within process {naucnikumetnik.capability_domain_id.process_id.name} ({naucnikumetnik.capability_domain_id.process_id.description}) and process area {naucnikumetnik.capability_domain_id.process_id.process_area_id.name} ({naucnikumetnik.capability_domain_id.process_id.process_area_id.description}) on a role {task.assignees.responsible.role} ({task.asignees.responsible.role_description}).
***Iteration***
This task has been already perfomed by you and it failed a review due to {task.hysteresis.failure_type}. This is the corrective action you should perform {task.hysteresis.corrective_action}.
This is the output you generated in that iteration:
{hysteresis.failed_output}
**Task**
***Name***
{task.name}
***Description***
{task.guideline.description}
***Steps***
{task.guideline.steps}
***Thinking checklist***
To help you structure thoughts, here's a thinking checklist:
{component.unit.heuristics.bundle}
***Method controls***

***Enablers***
This task is automated within {enabler.enabler_card.environment} environment. This script can {enabler.enabler_card.purpose}. If purpose of the enabler is not covering all the aspects needed to complete the activity, use the part that is automated and the rest do yourself. Call an enabler script by returning the correct command from guideline:
{enabler.guideline} 
***Inputs***
- {interface_id.card.name}:
{interface_id}  <!-- Full interface -->
***Hysteresis inputs***
***Outputs***
- {interface_id.card.name}:
{interface_id}  

Formatting type: {task.outputs.formatting.format_type}
Formatting rules:
- {capability_domain.format_type.control_bundle[i].statement}

Styling rules:
- {capability_domain.style_type.control_bundle[i].id}

Template:
- {template_id} <!-- Full template with description of each field -->
Schema rules:
- {unit.controls.schema}
Enum rules:
- {unit.controls.enum}
Validation rules:
- {unit.controls.validation}
Example: <!-- Full example-->
Bad example: <!-- Full bad example-->
***Acceptance criteria***

**Constrains**
- No chit-chat, only what was asked with controls applied
