# API reference

## PeachTrees

::: peachtrees.PeachTrees
    options:
      members:
        - fit
        - forward
        - explain
        - run_batch
        - abatch
        - cost_report
        - save_fit
        - load_fit

::: peachtrees.Selection

## Task adapters

::: peachtrees.tasks
    options:
      members:
        - Task
        - math
        - choice
        - sql
        - code
        - plan
        - free_text
        - SQLiteDB

## Verifier

::: peachtrees.Verifier

::: peachtrees.VerifierGate

## Selection rules and task switches

::: peachtrees.pick

::: peachtrees.contested

::: peachtrees.do_no_harm

::: peachtrees.non_inferiority

::: peachtrees.switch_power

::: peachtrees.paired_stats

::: peachtrees.text_key

## Observability and cost

::: peachtrees.Callback

::: peachtrees.LoggingCallback

::: peachtrees.JSONLCallback

::: peachtrees.Ledger

## Offline replay

::: peachtrees.replay

## Forms and tools

::: peachtrees.Assembled

::: peachtrees.Liquid

::: peachtrees.run_python

::: peachtrees.item_tool
