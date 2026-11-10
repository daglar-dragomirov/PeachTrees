"""The fixed texts of PeachTrees. They are the same for every task; changing them changes the method."""

# The free (liquid) agent: solves the task from scratch with the task's tools and run_python.
LIQUID_TEMPLATE = (
    "Accomplish the task described above for the given inputs. Work step by step. If the task depends on information you "
    "do not have, gather it with the available tools first: make several targeted searches or calls, start from what the "
    "inputs name, follow leads found in the results, and base your output on what you found. Use run_python (Python, "
    "standard library only, no network) for any calculation, counting or check. Before giving the final output, check it "
    "against every requirement of the task and fix anything that is wrong or missing. Give the final output in the "
    "required format.")

# The assembled form: checks and repairs the draft of the optimized program.
ASSEMBLED_TEMPLATE = (
    "A fixed pipeline already produced a draft for this task (given in the inputs). Check the draft against every "
    "requirement of the task. If something the task depends on is missing or wrong in the draft, gather what is needed "
    "with the available tools (targeted searches or calls, following leads found in the results) and fix it; use "
    "run_python (Python, standard library only, no network) for any calculation, counting or check. If the draft is "
    "correct, return it unchanged; if you change it, keep its form and length. If you can neither confirm nor fix it, "
    "return the draft unchanged; never replace it with a statement that the answer cannot be determined. Give the final "
    "output in the required format.")

# The asymmetric judge: keeps the reference (default form) unless it can name a checkable defect.
JUDGE_TEMPLATE = (
    "Several solvers independently produced outputs for the same task. The reference output comes from the solver chosen "
    "in advance as the most reliable one; each output is shown with the record of how it was produced. Keep the reference "
    "unless you can name one specific, checkable defect in it that matters for the task's purpose - a requirement of the "
    "task missed or violated, a factual, logical or calculation error, or an output in the wrong form - and one "
    "alternative is free of that defect without adding a new one. Outputs that are merely different, longer, more "
    "detailed or more confident are not evidence; if you are unsure, answer KEEP. Write the defect (or 'none'), then "
    "answer KEEP, A or B.")

# Fields a judge must never see: anything derived from gold labels or a grader (scores, checker verdicts, rewards).
HIDDEN_FIELDS = ("check", "score", "reward", "gold", "label", "verdict")


def purpose_of(program):
    """The task's purpose as the base program itself defines it: its predictors' own signature instructions."""
    return "\n".join(f"- {p.signature.instructions.strip()}" for _, p in program.named_predictors())


def form_instructions(purpose, guidance=None, examples=None):
    """Instructions of the liquid and assembled forms: the task's purpose, the optimizer's learned guidance (if any),
    correct output examples (if any) and one fixed template per form."""
    head = "The task:\n" + purpose
    if guidance:
        head += "\n\nGuidance learned for this task by an optimizer (apply it where it fits):\n" + guidance
    if examples:
        head += ("\n\nCorrect final outputs for other inputs of this task (follow their form and length; no "
                 "explanations unless they show some):\n" + examples)
    return {"liquid": head + "\n\n" + LIQUID_TEMPLATE, "assembled": head + "\n\n" + ASSEMBLED_TEMPLATE}
