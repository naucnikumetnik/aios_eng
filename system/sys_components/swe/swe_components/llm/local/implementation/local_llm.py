import logging
import time
from dataclasses import dataclass

from llama_cpp import (
    Llama,
    llama_supports_gpu_offload,   # low-level capability check
)

# ---- basic logging setup ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@dataclass
class LLMConfig:
    model_path: str
    n_ctx: int = 16384          # you can bump this towards 32768 if RAM/VRAM allows
    n_gpu_layers: int = -1     # "all layers" *if* GPU offload is actually available
    n_batch: int = 512
    n_threads: int = 16

    temperature: float = 0.25
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    max_tokens: int = 2048


class LLMEngine:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

        # ---- check if this build even supports GPU ----
        gpu_supported = llama_supports_gpu_offload()
        logging.info("llama-cpp GPU offload supported by this build: %s", gpu_supported)

        if not gpu_supported:
            logging.warning(
                "This llama-cpp-python build does NOT support GPU offload. "
                "n_gpu_layers=%s will be ignored and everything runs on CPU. "
                "To fix: reinstall with GPU support, e.g.: "
                "`pip install --upgrade --force-reinstall llama-cpp-python[cuda]`",
                cfg.n_gpu_layers,
            )

        # ---- init model (verbose=True prints backend info: CUDA/CPU, layers, etc.) ----
        t0 = time.perf_counter()
        self.llm = Llama(
            model_path=cfg.model_path,
            n_ctx=cfg.n_ctx,
            n_gpu_layers=cfg.n_gpu_layers,
            n_batch=cfg.n_batch,
            n_threads=cfg.n_threads,
            verbose=True,  # this will print whether CUDA / Metal / CPU backend is used
        )
        t1 = time.perf_counter()
        logging.info(
            "Model loaded from '%s' in %.2f s (n_ctx=%d, n_gpu_layers=%d, n_batch=%d, n_threads=%d)",
            cfg.model_path,
            t1 - t0,
            cfg.n_ctx,
            cfg.n_gpu_layers,
            cfg.n_batch,
            cfg.n_threads,
        )

    def run(self, *, system_prompt: str, user_prompt: str, extra_context: str = "") -> str:
        """
        extra_context is where future RAG output will be injected.
        For now you can just concatenate it.
        """
        full_user = user_prompt
        if extra_context:
            full_user = (
                "Additional context:\n"
                + extra_context.strip()
                + "\n\nTask:\n"
                + user_prompt.strip()
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user},
        ]

        # ---- timing the actual inference ----
        t0 = time.perf_counter()
        out = self.llm.create_chat_completion(
            messages=messages,
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
            repeat_penalty=self.cfg.repeat_penalty,
            max_tokens=self.cfg.max_tokens,
        )
        t1 = time.perf_counter()

        elapsed = t1 - t0
        usage = out.get("usage", {}) or {}
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")

        # crude tokens/s – only completion tokens are interesting for generation speed
        tok_s = None
        if completion_tokens is not None and elapsed > 0:
            tok_s = completion_tokens / elapsed

        logging.info(
            "Inference finished in %.2f s | prompt=%s, completion=%s, total=%s, gen_speed=%s tok/s",
            elapsed,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            f"{tok_s:.1f}" if tok_s is not None else "n/a",
        )

        return out["choices"][0]["message"]["content"]


if __name__ == "__main__":
    cfg = LLMConfig(
        model_path="/home/bratislav/Documents/LLMs/models/Meta-Llama-3-8B-Instruct.Q8_0.gguf",
        # tune these once GPU is actually confirmed
        n_ctx=16384,
        n_gpu_layers=-1,
        n_batch=512,
        n_threads=16,
    )

    engine = LLMEngine(cfg)

    system_prompt = "You are a precise software and process architect. Follow the instructions exactly."
    user_prompt = """
**System**
You're working within naucnikumetnik system.
It is automated, standards aligned, machine readable company system run by LLMs.
**Project**
You're working on the system itself.
**Task metadata**
***Process area***
You're working within engineering capability domain within software process and process area SWE.3 (ASPICE aligned) on a role software architect.
**Task**
***Name***
Define interface spec
***Description***
Derive interface_spec artifact for a given domain from the architecture_description and surrounding context.
***Steps***
    0. Read selection
       0.1. Read the interface selection payload from IF.interface_selection.
       0.2. Extract:
            - requested_interface_id (if provided)
            - requested_connector_index (if provided)
            - generation_mode (default "create_or_replace").

    1. Resolve architecture context
       1.1. Read architecture_description.card.id and card.domain.
       1.2. Enumerate connectors from:
            views.structural.elements.connectors[*].
       1.3. For each connector, collect:
            - connector.interface_id
            - connector.purpose
            - participating units and their interaction_type.

    2. Locate the target connector
       2.1. If requested_interface_id is provided:
            - Filter connectors where connector.interface_id == requested_interface_id.
            - If exactly one match: select that connector.
            - If zero matches: fail with "E_IF_NOT_FOUND" and abort generation.
            - If multiple matches:
              - If requested_connector_index is provided and within bounds of the
                filtered subset: pick that one.
              - Otherwise: fail with "E_IF_AMBIGUOUS" and abort generation.
       2.2. Else if requested_connector_index is provided:
            - Select connectors[requested_connector_index] if in range.
            - If out of range: fail with "E_IF_INDEX_INVALID" and abort generation.
       2.3. If neither requested_interface_id nor requested_connector_index is
            provided: fail with "E_IF_SELECTION_MISSING".

    3. Initialize interface_spec skeleton
       3.1. Initialize card:
            - card.id :=
                project-defined unique id, e.g. "<arch_id>.<interface_id>.if.0v1"
            - card.name :=
                human-readable label derived from connector.purpose or interface_id.
            - card.domain :=
                architecture_description.card.domain (or "meta" for meta-domain),
                unless overridden by project configuration.
            - card.interface_id :=
                target connector.interface_id.
            - card.related_architecture_id :=
                architecture_description.card.id.
       3.2. Initialize kind:
            - kind.role :=
                free-text classification (e.g. "design-time meta interface",
                "system runtime interface", "software runtime interface")
                derived from card.domain and project heuristics.

    4. Set purpose
       4.1. purpose.description :=
            short free-text based on:
            - connector.purpose, if available
            - participating units and their interaction_type
            - optional project/domain conventions (e.g. "exchange of UDD artifacts").

    5. Set binding (when applicable)
       5.1. For meta-domain connectors known to carry whole workproducts
            (e.g. IF.architecture_description, IF.unit_detailed_design,
            IF.integration_plan_skeleton), set:
            - binding.artifact_kind :=
                corresponding artifact_kind (e.g. "architecture_description").
            - binding.artifact_schema_version :=
                known schema version when available (e.g. "0.1").
            - binding.artifact_path := "" (full-artifact transfer).
       5.2. For other connectors (runtime signals, commands, events) leave
            binding.artifact_kind empty at 0v1, and rely on data_semantics.payloads
            to describe the payload structure.

    6. Initialize interaction
       6.1. interaction.style:
            - choose a style based on connector role and domain:
              - meta artifact exchange  -> "reference input" or "config interface"
              - request/command-like    -> "command API"
              - continuous values       -> "signal bus"
              - pub/sub events          -> "event stream"
            - ensure value conforms to ENUM.interface_spec.interaction.style.
       6.2. interaction.direction:
            - if exactly one outbound unit and >=1 inbound units: "unidirectional".
            - if conceptually request/response: "bidirectional".
            - otherwise: leave empty at 0v1 and clarify in purpose/notes.
       6.3. interaction.contract:
            - preconditions, effects, sequencing, timing:
              free text using reusable patterns tied to interaction.style,
              e.g.:
              - command API: "preconditions: target unit initialized",
                "sequencing: command before start"
              - reference input: "preconditions: artifact is valid and baselined",
                etc.

    7. Initialize data_semantics (0v1)
       7.1. If binding.artifact_kind is set:
            - create a single payload:
              - payload.id          := "artifact"
              - payload.name        := "<artifact_kind> payload"
              - payload.direction   := "provider_to_consumer"
              - payload.description := "Complete <artifact_kind> artifact as defined by its schema."
              - payload.fields      := [] (no duplication of artifact schema).
       7.2. If binding.artifact_kind is empty and connector is runtime-data:
            - create one or more payloads with minimal field definitions:
              - field.id, field.name, field.type
              - required, range, unit when known.
            - enforce uniqueness of payload.id and fields[*].id.

    8. Initialize error_model (single-interface focus)
       8.1. Always include basic selection errors:
            - E_IF_NOT_FOUND
            - E_IF_AMBIGUOUS
            - E_IF_INDEX_INVALID
            - E_IF_SELECTION_MISSING
       8.2. For design-time/meta interfaces:
            - optionally add generic errors:
              - E_NOT_FOUND, E_INVALID, E_BACKEND_FAILURE.
       8.3. For runtime interfaces:
            - extend with domain-specific errors consistent with enum controls:
              - category in {"timeout", "validation", "internal"}.
              - severity in {"info", "warning", "error", "fatal"}.
            - ensure codes are unique per interface_spec.

    9. Initialize observability
       9.1. logs.required_fields:
            - at minimum:
              - "timestamp"
              - "interface_id"
              - "domain_id" (if available)
              - "arch_id"
              - "producer_unit_id"
              - "consumer_unit_id"
              - "result_code"
       9.2. health_signals:
            - for critical interfaces, define:
              - e.g. "if_exchange_success_rate"
              - description and update_period suitable for CI or nightly checks.

    10. Initialize traceability
       10.1. traceability.requirements_ref:
             - link to requirement ids or patterns that defined the need for this
               interface, when available.
       10.2. traceability.concerns_ref:
             - map to concerns from the associated architecture_description
               that drove the interface design (e.g. C-COV-01, C-CON-01).
       10.3. For baselined artifacts, traceability SHALL NOT be left empty.

    11. Apply control bundles
       11.1. Evaluate:
             - controls.interface_spec.schema.0v1
             - controls.interface_spec.enum.0v1
             - controls.interface_spec.validators.0v1
             against the generated interface_spec.
       11.2. If any mandatory control (SHALL) fails:
             - mark generation as failed for this interface,
             - do not publish the artifact via IF.interface_spec.
       11.3. SHOULD-level suggestions MAY be logged as warnings but do not block
             generation at 0v1.

    12. Persist and expose
       12.1. Store the generated interface_spec artifact in the configured repository
             path for the domain, applying generation_mode:
             - "create_only": fail if an artifact with the same card.id exists.
             - "replace": overwrite existing artifact.
             - "create_or_replace": create or overwrite.
       12.2. Announce availability via IF.interface_spec so that:
             - U.def_int (integration plan) and
             - U.def_udd (UDD generation)
             can consume the interface_spec.
***Thinking checklist***
To help you structure thoughts, here's a thinking checklist:
    - When connector.purpose is present, use it as the starting point for purpose.description and refine only if needed; do not attempt to over-normalize the wording at 0v1.
    - For meta-domain connectors known to carry entire workproducts, prefer expressing payloads as a single "artifact" payload with binding.artifact_kind set, instead of duplicating artifact schema fields in data_semantics.
    - Default interaction.style based on unit roles:
        - from architecture-definition units to other meta-units: "reference input"
        - from runtime controllers to services: "command API" or "query API"
        - from sensors or streams: "signal bus" or "event stream"
    - If there is exactly one producer and one consumer unit for a connector, default interaction.direction to "unidirectional"; otherwise, leave direction empty in 0v1 and document the pattern in purpose.description.
    - When unsure about error_model for a design-time interface in 0v1, prefer leaving error_model.codes empty rather than inventing poorly-defined error codes; add them later when real failure modes are observed.
    - For logs.required_fields, always include at least "interface_id" and "timestamp"; add one or more domain-specific correlation fields (e.g. "domain_id", "arch_id") whenever available.
    - Treat "SHALL" controls in schema/validators as strict; treat "SHOULD" enum controls as guidance that can be overridden with explicit justification.
***Inputs***
- Architecure description views:
  structural:
    description: 'Meta-units and information flow between them for domain definition and CM binding.'
    viewpoint_ref: 'VP-struct'
    concerns_ref: ['C-COV-01', 'C-CON-01', 'C-CM-01']
    elements:
      units:
        - unit_id: 'U.def_sys_req'
          unit_name: 'Define sys req'
          role: 'Define system/software requirements and domain constraints for domains.'
          notes: 'External to FDB system_of_interest; provides input context only.'
        - unit_id: 'U.def_arch'
          unit_name: 'Define architecture description'
          role: 'Assemble architecture_description from requirements + domain model.'
          notes: ''
        - unit_id: 'U.def_if'
          unit_name: 'Define interface spec'
          role: 'Derive interface_spec from architecture connectors + context.'
          notes: ''
        - unit_id: 'U.def_udd'
          unit_name: 'Define UDD'
          role: 'Derive UDD for each unit from architecture + interface_spec + integration plan hints.'
          notes: ''
        - unit_id: 'U.def_int'
          unit_name: 'Define integration plan'
          role: 'Derive integration_plan from architecture + interface_spec + domain constraints.'
          notes: ''
        - unit_id: 'U.def_cm_catalogue'
          unit_name: 'Define CM domain catalogue'
          role: 'Define and maintain CM domain catalogue (list of configuration items) for a project/domain.'
          notes: 'External CM component; provides cm_domain_catalogue to this meta-component.'
        - unit_id: 'U.perform_cm_binding'
          unit_name: 'Perform CM binding'
          role: 'Create and maintain cm_unit_binding artifacts linking domain units/workproducts to configuration items.'
          notes: ''
        - unit_id: 'U.cm_consumer'
          unit_name: 'CM consumer'
          role: 'Consumes cm_unit_binding artifacts for release, audit, and status accounting.'
          notes: 'External to this meta-component.'
      connectors:
        - interface_id: 'IF.arch_desc_context'
          purpose: 'Relevant system/software requirements and domain constraints for architecture definition.'
          units:
          - unit_id: 'U.def_sys_req'
            unit_name: 'Define sys req'
            interaction_type: outbound
          - unit_id: 'U.def_arch'
            unit_name: 'Define architecture description'
            interaction_type: inbound
        - interface_id: 'IF.architecture_description'
          purpose: 'Architecture description 0v1 (units, connectors, groupings, constraints).'
          units:
          - unit_id: 'U.def_arch'
            unit_name: 'Define architecture description'
            interaction_type: outbound
          - unit_id: 'U.def_if'
            unit_name: 'Define interface spec'
            interaction_type: inbound
          - unit_id: 'U.def_int'
            unit_name: 'Define integration plan'
            interaction_type: inbound
          - unit_id: 'U.def_udd'
            unit_name: 'Define UDD'
            interaction_type: inbound
        - interface_id: 'IF.interface_spec'
          purpose: 'Interface specifications 0v1 for each connector.'
          units:
          - unit_id: 'U.def_if'
            unit_name: 'Define interface spec'
            interaction_type: outbound
          - unit_id: 'U.def_int'
            unit_name: 'Define integration plan'
            interaction_type: inbound
          - unit_id: 'U.def_udd'
            unit_name: 'Define UDD'
            interaction_type: inbound
        - interface_id: 'IF.integration_plan_skeleton'
          purpose: 'Initial integration strategy and stages to guide unit test design.'
          units:
          - unit_id: 'U.def_int'
            unit_name: 'Define integration plan'
            interaction_type: outbound
          - unit_id: 'U.def_udd'
            unit_name: 'Define UDD'
            interaction_type: inbound
        - interface_id: 'IF.unit_detailed_design'
          purpose: 'Detailed unit description.'
          units:
          - unit_id: 'U.def_udd'
            unit_name: 'Define UDD'
            interaction_type: outbound
          - unit_id: 'U.def_int'
            unit_name: 'Define integration plan'
            interaction_type: inbound
          - unit_id: 'U.perform_cm_binding'
            unit_name: 'Perform CM binding'
            interaction_type: inbound
        - interface_id: 'IF.cm_domain_catalogue'
          purpose: 'CM domain catalogue for this project/domain, containing configuration items and their attributes.'
          units:
          - unit_id: 'U.def_cm_catalogue'
            unit_name: 'Define CM domain catalogue'
            interaction_type: outbound
          - unit_id: 'U.perform_cm_binding'
            unit_name: 'Perform CM binding'
            interaction_type: inbound
        - interface_id: 'IF.cm_unit_binding'
          purpose: 'CM binding artifacts linking domain units/workproducts to configuration items.'
          units:
          - unit_id: 'U.perform_cm_binding'
            unit_name: 'Perform CM binding'
            interaction_type: outbound
          - unit_id: 'U.cm_consumer'
            unit_name: 'CM consumer'
            interaction_type: inbound

  dynamic:
    description: 'Happy path: define domain artifacts from requirements. CM binding is fed by UDD and CM catalogue; detailed CM scenarios live in the UDD of U.perform_cm_binding at 0v1.'
    viewpoint_ref: 'VP-dynamic'
    concerns_ref: ['C-CHG-01', 'C-USR-01', 'C-COV-01', 'C-CON-01']
    scenarios:
    - scenario_id: 'S-DEF-01'
      description: 'Define domain artifacts for a new domain from existing requirements.'
      trigger: 'User initiates domain definition for domain X.'
      covered_requirements: ['REQSET.FDB.DOMAIN_DEF.*']
      covered_concerns: ['C-COV-01', 'C-CON-01', 'C-CHG-01', 'C-USR-01']
      primary_flow:
      - step_id: '1'
        interface_id: 'IF.arch_desc_context'
        from_unit_id: 'U.def_sys_req'
        to_unit_id: 'U.def_arch'
        notes: 'Requirements and domain constraints are provided to architecture definition.'
      - step_id: '2'
        interface_id: 'IF.architecture_description'
        from_unit_id: 'U.def_arch'
        to_unit_id: 'U.def_if'
        notes: 'Initial architecture_description is provided to interface spec definition.'
      - step_id: '3'
        interface_id: 'IF.architecture_description'
        from_unit_id: 'U.def_arch'
        to_unit_id: 'U.def_int'
        notes: 'Initial architecture_description is provided to integration plan definition.'
      - step_id: '4'
        interface_id: 'IF.architecture_description'
        from_unit_id: 'U.def_arch'
        to_unit_id: 'U.def_udd'
        notes: 'Initial architecture_description is provided to UDD definition.'
      - step_id: '5'
        interface_id: 'IF.interface_spec'
        from_unit_id: 'U.def_if'
        to_unit_id: 'U.def_int'
        notes: 'Interface specifications are provided to integration plan definition.'
      - step_id: '6'
        interface_id: 'IF.interface_spec'
        from_unit_id: 'U.def_if'
        to_unit_id: 'U.def_udd'
        notes: 'Interface specifications are provided to UDD definition.'
      - step_id: '7'
        interface_id: 'IF.integration_plan_skeleton'
        from_unit_id: 'U.def_int'
        to_unit_id: 'U.def_udd'
        notes: 'Integration plan skeleton guides UDD test design and refinement.'
      - step_id: '8'
        interface_id: 'IF.unit_detailed_design'
        from_unit_id: 'U.def_udd'
        to_unit_id: 'U.def_int'
        notes: 'Final UDDs are provided back to integration plan for consistency and coverage checks.'
      - step_id: '9'
        interface_id: 'IF.unit_detailed_design'
        from_unit_id: 'U.def_udd'
        to_unit_id: 'U.perform_cm_binding'
        notes: 'UDDs are provided to CM binding so units/workproducts can be mapped to configuration items.'
      notes: 'Represents the main design-time flow across meta-units. Consumption of cm_domain_catalogue and emission of cm_unit_binding are handled by U.perform_cm_binding and detailed in its UDD.'

- IF.interface_selection.requested_interface_id = 'IF.architecture_description'
- IF.interface_selection.generation_mode = create

***Output configuration***
****asdas****Formatting type: yaml
Template:
    artifact_kind: interface_spec
    schema_version: '0.1'

    card:
    id: ''
    name: ''
    domain: ''                # 'system' | 'software' | 'meta' | ...
    interface_id: ''
    related_architecture_id: ''

    kind:
    role: ''                  # 'design-time meta interface', 'runtime API', 'config interface', ...

    purpose:
    description: ''

    binding:
    artifact_kind: ''         # e.g. 'architecture_description', 'unit_detailed_design', 'integration_plan'
    artifact_schema_version: ''  # optional
    artifact_path: ''         # optional path inside the artifact if only a subset travels here

    interaction:
    style: ''                 # 'command API', 'signal bus', 'event stream', 'reference input', ...
    direction: ''             # 'unidirectional' | 'bidirectional' | '' (optional)
    contract:
        preconditions: ''
        effects: ''
        sequencing: ''
        timing: ''

    data_semantics:
    payloads:
        - id: ''
        name: ''
        direction: ''         # 'provider_to_consumer' | 'consumer_to_provider' | ''
        description: ''
        fields:
            - id: ''
            name: ''
            type: ''          # free-form: 'int', 'float', 'bool', 'string', 'json', ...
            unit: ''          # optional
            required: false
            range: ''         # free-text constraints
            description: ''
    notes: ''

    error_model:
    codes:
        - code: ''
        description: ''
        category: ''          # 'timeout', 'validation', 'internal', ...
        severity: ''          # 'info', 'warning', 'error', 'fatal'
        recoverable: false
    behavior: ''              # overall error semantics (retry, backoff, etc.)

    observability:
    logs:
        required_fields:
        - ''                  # e.g. 'trace_id', 'interface_id', ...
        notes: ''
    health_signals:
        - id: ''
        description: ''
        update_period: ''

    traceability:
    requirements_ref: ''
    concerns_ref: []

    Schema rules:
    - {unit.controls.schema}
    Enum rules:
    - {unit.controls.enum}
    Validation rules:
    - {unit.controls.validation}

Schema rules:
  - 'Field artifact_kind SHALL be a scalar string identifying the artifact kind.'
  - Field schema_version SHALL be a scalar string representing the schema version of the interface_spec.'
  - 'Field card SHALL be a mapping containing identity and classification fields for the interface_spec.'
  - 'Field card.id SHALL be a scalar string uniquely identifying the interface_spec artifact within its repository.'
  - 'Field card.name SHALL be a scalar string providing a human-readable name for the interface_spec.'
  - 'Field card.domain SHALL be a scalar string indicating the domain in which the interface is used (for example, "system", "software", or "meta").'
  - 'Field card.interface_id SHALL be a scalar string equal to the technical identifier of the interface described (as used in architecture_description.connectors.interface_id).'
  - 'Field card.related_architecture_id SHALL be a scalar string referencing the associated architecture_description.card.id, or an empty string when not applicable.'
  - 'Field kind SHALL be a mapping grouping classification aspects of the interface.'
  - 'Field kind.role SHALL be a scalar string describing the role of the interface (for example, "design-time meta interface" or "runtime API").'
  - 'Field purpose SHALL be a mapping capturing the high-level intent of the interface.'
  - 'Field purpose.description SHALL be a scalar string describing, in free text, the purpose of the interface.'
  - 'Field binding SHALL be a mapping describing which artifact kind is transported by this interface, when applicable.'
  - 'Field binding.artifact_kind SHALL be a scalar string naming the artifact_kind transported by this interface, or an empty string when the interface does not transport a structured artifact.'
  - 'Field binding.artifact_schema_version SHALL be a scalar string indicating the schema version of the transported artifact, or an empty string when not specified.'
  - 'Field binding.artifact_path SHALL be a scalar string indicating a path within the transported artifact when only a subset is transported, or an empty string when the whole artifact is transported.'
  - 'Field interaction SHALL be a mapping describing the interaction pattern and contract of the interface.'
  - 'Field interaction.style SHALL be a scalar string naming the interaction style (for example, "command API", "signal bus", "event stream", or "reference input").'
  - 'Field interaction.direction SHALL be a scalar string indicating the information-flow direction (for example, "unidirectional" or "bidirectional"), or an empty string when not constrained.'
  - 'Field interaction.contract SHALL be a mapping capturing preconditions, effects, sequencing, and timing expectations for the interface.'
  - 'Field interaction.contract.preconditions SHALL be a scalar string describing the conditions under which the interface may be used.'
  - 'Field interaction.contract.effects SHALL be a scalar string describing the high-level observable effects of using the interface.'
  - 'Field interaction.contract.sequencing SHALL be a scalar string describing any ordering rules between uses of this interface and other actions.'
  - 'Field interaction.contract.timing SHALL be a scalar string describing timing expectations (for example, latency or period), or an empty string when timing is not constrained.'
  - 'Field data_semantics SHALL be a mapping describing the payload structure and meaning for this interface.'
  - 'Field data_semantics.payloads SHALL be a sequence (list) of payload definitions, each being a mapping.'
  - 'Each payload.id SHALL be a scalar string uniquely identifying that payload within the interface_spec.'
  - 'Each payload.name SHALL be a scalar string providing a human-readable name for the payload.'
  - 'Each payload.direction SHALL be a scalar string indicating payload flow direction (for example, "provider_to_consumer" or "consumer_to_provider"), or an empty string when not constrained.'
  - 'Each payload.description SHALL be a scalar string describing the purpose and content of the payload.'
  - 'Each payload.fields SHALL be a sequence (list) of field definitions, each being a mapping.'
  - 'Each field.id in a payload SHALL be a scalar string uniquely identifying that field within the payload.'
  - 'Each field.name in a payload SHALL be a scalar string providing a human-readable name for the field.'
  - 'Each field.type in a payload SHALL be a scalar string indicating the field type (for example, "int", "float", "bool", "string", or "json").'
  - 'Each field.unit in a payload SHALL be a scalar string naming the measurement unit when applicable, or an empty string when not applicable.'
  - 'Each field.required in a payload SHALL be a boolean flag indicating whether the field is mandatory (true) or optional (false).'
  - 'Each field.range in a payload SHALL be a scalar string describing any value constraints or accepted ranges for the field, or an empty string when unconstrained.'
  - 'Each field.description in a payload SHALL be a scalar string describing the meaning and usage of the field.'
  - 'Field data_semantics.notes SHALL be a scalar string for additional free-text notes about payload semantics, or an empty string when not used.'
  - 'Field error_model SHALL be a mapping describing error codes and behavior for this interface.'
  - 'Field error_model.codes SHALL be a sequence (list) of error-code definitions, each being a mapping.'
  - 'Each error_model.codes[].code SHALL be a scalar string uniquely identifying the error code within this interface.'
  - 'Each error_model.codes[].description SHALL be a scalar string describing the error condition.'
  - 'Each error_model.codes[].category SHALL be a scalar string indicating a coarse error category (for example, "timeout", "validation", or "internal"), or an empty string when not classified.'
  - 'Each error_model.codes[].severity SHALL be a scalar string indicating severity (for example, "info", "warning", "error", or "fatal").'
  - 'Each error_model.codes[].recoverable SHALL be a boolean flag indicating whether the error condition is considered recoverable (true) or not (false).'
  - 'Field error_model.behavior SHALL be a scalar string describing the overall error-handling semantics for the interface.'
  - 'Field observability SHALL be a mapping describing logging and health-signal expectations for the interface.'
  - 'Field observability.logs SHALL be a mapping describing logging requirements for the interface.'
  - 'Field observability.logs.required_fields SHALL be a sequence (list) of scalar strings naming log fields that SHALL be present in logs for this interface.'
  - 'Field observability.logs.notes SHALL be a scalar string for additional free-text notes about logging, or an empty string when not used.'
  - 'Field observability.health_signals SHALL be a sequence (list) of health-signal definitions, each being a mapping.'
  - 'Each observability.health_signals[].id SHALL be a scalar string uniquely identifying the health signal.'
  - 'Each observability.health_signals[].description SHALL be a scalar string describing the purpose and meaning of the health signal.'
  - 'Each observability.health_signals[].update_period SHALL be a scalar string describing how often the health signal is expected to be updated.'
  - 'Field traceability SHALL be a mapping describing links from this interface_spec to requirements and concerns.'
  - 'Field traceability.requirements_ref SHALL be a scalar string referencing one or more requirement identifiers or patterns associated with this interface.'
  - 'Field traceability.concerns_ref SHALL be a sequence (list) of scalar strings referencing concern identifiers that this interface_spec helps address.'

Enum rules:
  - Field card.domain SHOULD be chosen from the set {"system", "software", "meta"} and MAY use other project-defined domain identifiers when these are documented in the domain catalog.
  - Field binding.artifact_kind SHOULD be set to one of the registered artifact kinds for the project; for 0v1 this includes at least:
      {"architecture_description", "interface_spec", "unit_detailed_design", "integration_plan"}.
  - Field interaction.style SHOULD use a controlled vocabulary; for 0v1 the recommended values are {"command API", "signal bus", "event stream", "reference input","config interface", "query API", "notification"} and MAY be extended with additional labels if consistently applied.
  - When interaction.direction is specified, it SHALL be one of {"unidirectional", "bidirectional"}; when left empty, the direction is treated as unspecified.
  - When a payload.direction is specified, it SHALL be one of {"provider_to_consumer", "consumer_to_provider"}; when left empty, direction is treated as unspecified.
  - When an error_model.codes[].category is specified, it SHOULD be chosen from {"timeout", "validation", "internal", "external", "resource", "protocol"} and MAY be extended with additional categories if documented in the error taxonomy.
  - When an error_model.codes[].severity is specified, it SHALL be one of {"info", "warning", "error", "fatal"}.
  - Field error_model.codes[].recoverable SHALL take values from the boolean domain {true, false}.
  - Field observability.health_signals[].update_period SHOULD use a consistent duration notation (for example, "1s", "10s", "1m", "1h") and MAY follow a project-wide duration format definition when available.
  - Each entry in traceability.concerns_ref SHOULD correspond to a valid concern.id defined in one or more architecture_description artifacts for the same project.
  - Field traceability.requirements_ref SHOULD contain one or more requirement identifiers or patterns conforming to the project’s requirement-id scheme (for example, "SYS-REQ-xxx", "SWE-REQ-xxx", or "REQSET.*") and SHALL NOT use arbitrary free-text labels.

Validation rules:
  - The field artifact_kind of an interface_spec artifact SHALL be set to the literal value "interface_spec".
  - Fields card.id, card.name and card.interface_id SHALL be non-empty strings
      so that the interface_spec and the interface it describes can be uniquely
      identified.
  - Field purpose.description SHOULD contain a meaningful description of the
      interface purpose and SHALL NOT be left as a placeholder such as "TBD" or
      "TODO" in released baselines.
  - An interface_spec SHALL describe the data it carries by providing at least
      one payload in data_semantics.payloads or a non-empty binding.artifact_kind
      (or both).
  - When binding.artifact_kind is non-empty and the interface is primarily transporting an artifact instance, either data_semantics.payloads SHALL contain a single payload describing the transport envelope for that artifact or data_semantics.payloads SHALL be empty and the binding SHALL be treated as describing a full-artifact transfer.
  - Field interaction.style SHALL be specified for every interface_spec to make the interaction pattern explicit.
  - When interaction.direction is set to "unidirectional", all payloads for the interface SHOULD use a payload.direction consistent with the chosen flow (for example, only "provider_to_consumer"), unless a deviation is explicitly justified in notes or documentation.
  - When binding.artifact_kind is empty, data_semantics.payloads SHALL contain at least one payload describing the data structure carried by the interface.
  - Each payload in data_semantics.payloads SHALL define non-empty values for payload.id, payload.name and payload.description.
  - Within a single interface_spec, all payload.id values SHALL be unique.
  - Each field in payload.fields SHALL define non-empty values for field.id,
      field.name and field.type.
  - Within a given payload, all field.id values in payload.fields SHALL be unique.
  - When field.required is true, the field.range and field.description SHOULD be specified with enough detail for a reviewer to understand expected value constraints; leaving both empty for required fields SHOULD be avoided in released baselines.
  - Each error_model.codes entry SHALL define a non-empty code and description so that error conditions can be uniquely identified and understood.
  - Within a single interface_spec, all error_model.codes[].code values SHALL be unique.
  - For interfaces that represent runtime interactions (for example, interaction.style in {"command API", "query API", "event stream"}), error_model.codes SHOULD not be empty and SHOULD at least cover typical failure modes for that interaction.
  - When observability.logs.required_fields is specified, each entry SHALL be a non-empty string naming a log field; empty or placeholder entries SHALL NOT be used.
  - Each health signal in observability.health_signals SHALL define a non-empty id and description; update_period SHOULD be provided for periodic metrics and MAY be left empty for event-based health signals.
  - When traceability.requirements_ref is populated, it SHALL NOT contain only placeholder markers such as "TBD" or "TODO" and SHOULD reference one or more concrete requirement identifiers or patterns valid in the project.
  - For interfaces classified as critical by project policy (for example, safety- or compliance-relevant interfaces), traceability.concerns_ref SHOULD not be empty and SHOULD reference the concerns that the interface helps address.
  - For interface_spec artifacts that declare a non-empty card.related_architecture_id, card.interface_id SHALL match the interface_id of at least one connector in the referenced architecture_description.
  - When binding.artifact_kind is non-empty and card.related_architecture_id refers to an architecture_description, binding.artifact_kind SHOULD be consistent with the artifact_kind used on the corresponding connectors or workproducts in that architecture (for example, an interface that carries architecture_description artifacts SHALL use binding artifact_kind="architecture_description").

Example:
artifact_kind: interface_spec
schema_version: '0.1'

card:
  id: 'IF.cm_unit_binding.meta.v0'
  name: 'CM unit binding distribution'
  domain: 'meta'                     # design-time meta tooling
  interface_id: 'IF.cm_unit_binding'
  related_architecture_id: 'meta_arch_desc'

kind:
  role: 'design-time meta interface for distributing cm_unit_binding artifacts to CM consumers'

purpose:
  description: >
    Provides cm_unit_binding artifacts, produced by the "Perform CM binding" unit,
    to downstream CM consumers (release, audit, status accounting) so they can see
    which units/artifacts are bound to which configuration items.

binding:
  artifact_kind: 'cm_unit_binding'
  artifact_schema_version: '0.1'
  artifact_path: ''                  # full cm_unit_binding artifact is transported

interaction:
  style: 'reference input'
  direction: 'unidirectional'
  contract:
    preconditions: >
      - A valid CM domain catalogue exists and is accessible via IF.cm_domain_catalogue.
      - Valid UDDs (and other relevant workproducts) exist for the units to be bound.
      - The "Perform CM binding" unit has successfully created or updated one or more
        cm_unit_binding artifacts.
    effects: >
      - CM consumers obtain cm_unit_binding artifacts describing the mapping between
        units/workproducts and configuration items.
      - No modifications to cm_unit_binding artifacts are performed via this interface;
        it is a read-only distribution mechanism from the perspective of consumers.
    sequencing: >
      - This interface SHALL be used after CM binding for the relevant units has been
        performed or updated.
      - Release and audit workflows SHOULD consume cm_unit_binding via this interface
        before declaring baselines or performing CM audits.
    timing: >
      Design-time / lifecycle-time interface with no hard real-time constraints.
      Invocations are typically triggered by change requests, baseline creation,
      or periodic CM updates.

data_semantics:
  payloads:
    - id: 'cm_binding_payload'
      name: 'CM unit binding artifact'
      direction: 'provider_to_consumer'   # U.perform_cm_binding -> CM consumers
      description: >
        A single cm_unit_binding artifact describing bindings for one unit or a
        small group of related units, depending on the chosen granularity.
      fields:
        - id: 'project_id'
          name: 'Project identifier'
          type: 'string'
          unit: ''
          required: true
          range: ''
          description: 'Identifier of the project these bindings belong to.'
        - id: 'domain_id'
          name: 'Domain identifier'
          type: 'string'
          unit: ''
          required: true
          range: ''
          description: 'Domain whose units are being bound (e.g. "software", "fdb-meta").'
        - id: 'binding_card_id'
          name: 'Binding card id'
          type: 'string'
          unit: ''
          required: true
          range: ''
          description: 'card.id of the cm_unit_binding artifact.'
        - id: 'binding_schema_version'
          name: 'Binding schema version'
          type: 'string'
          unit: ''
          required: true
          range: ''
          description: 'Schema version of the cm_unit_binding artifact (e.g. "0.1").'
        - id: 'binding_body'
          name: 'CM unit binding payload'
          type: 'yaml'
          unit: ''
          required: true
          range: ''
          description: >
            Serialized cm_unit_binding artifact conforming to the cm_unit_binding
            schema. For 0v1 this is the full artifact (unit identifiers, workproduct ids,
            CI ids, binding attributes, etc.).
  notes: >
    At 0v1, one payload corresponds to one cm_unit_binding artifact. Whether that artifact
    covers a single unit or a set of units is up to the binding schema and project policy.

error_model:
  codes:
    - code: 'E_CM_BINDING_NOT_FOUND'
      description: 'Requested cm_unit_binding artifact does not exist for the given project/domain/identifier.'
      category: 'validation'
      severity: 'error'
      recoverable: true
    - code: 'E_CM_BINDING_INVALID'
      description: 'cm_unit_binding artifact exists but fails schema or validation controls.'
      category: 'validation'
      severity: 'error'
      recoverable: false
    - code: 'E_CM_BINDING_BACKEND_FAILURE'
      description: 'Internal failure while retrieving or serializing cm_unit_binding.'
      category: 'internal'
      severity: 'error'
      recoverable: true
  behavior: >
    - E_CM_BINDING_NOT_FOUND: CM consumers MAY request that CM binding be performed
      or updated before proceeding with release/audit activities.
    - E_CM_BINDING_INVALID: CM consumers SHALL NOT treat bindings as valid; the issue
      SHALL be corrected at the binding source before further use.
    - E_CM_BINDING_BACKEND_FAILURE: consumers MAY retry according to project-wide
      backoff policy; repeated failures SHOULD be logged and investigated as tooling issues.

observability:
  logs:
    required_fields:
      - 'timestamp'
      - 'interface_id'
      - 'project_id'
      - 'domain_id'
      - 'binding_card_id'
      - 'producer_unit_id'
      - 'consumer_unit_id'
      - 'result_code'
    notes: >
      Every use of IF.cm_unit_binding SHALL be logged with at least the required fields.
      Logs SHOULD allow reconstruction of which bindings were visible to which CM
      consumers at which point in time.
  health_signals:
    - id: 'cm_binding_distribution_success_rate'
      description: 'Ratio of successful cm_unit_binding transfers to total attempts.'
      update_period: 'aggregated per CI run or per day'
    - id: 'cm_binding_invalid_rate'
      description: 'Fraction of cm_unit_binding artifacts rejected due to validation failures.'
      update_period: 'aggregated per CI run or per day'

traceability:
  requirements_ref: 'REQSET.FDB.CM.BINDING.*'
  concerns_ref:
    - 'C-CM-01'
    - 'C-CON-01'

**Constrains**
- No chit-chat, only what was asked with controls applied


"""

    print(engine.run(system_prompt=system_prompt, user_prompt=user_prompt))


    answer = engine.run(system_prompt=system_prompt, user_prompt=user_prompt)
    print("=== MODEL OUTPUT ===")
    print(answer)
