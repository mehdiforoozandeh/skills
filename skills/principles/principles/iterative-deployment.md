# iterative-deployment

## Principle
Deploy the results of a long-running research task in iterations. Do not compile the whole
work in one shot.

- Think of the work as a research paper. The paper is not written in one pass. Its parts
  are presented one after the other, and each part grows over the iterations.
- The first long instruction set of a project is the background and the introduction of
  the paper.
- The Methods section comes next. It is developed gradually: the data, the evaluation,
  the model.
- Results, discussion and conclusions are added little by little, as each one is ready.
- Each iteration ends with a meaningful, reasonable piece of scientific progress that
  stands on its own, i.e. a result or an insight that can be shown.
- Use the fewest iterations possible. Inside each iteration, parallelize as much as
  possible. An iteration is defined by its set of parallel paths, i.e. runs and objectives
  that are pursued at the same time. Put the maximum number of parallel paths in each
  iteration; start a new iteration only for work that needs the results of the one before.
- Aim for good, conclusive results early, in days. Scale the ambition of an iteration down
  until it fits. The more time-consuming parts move to later phases, for the completion of
  the work.

## Why
A plan that delivers only at the end, after weeks, gives no result and no insight on the
way, and a late blocker costs the whole plan. Short iterations give results that can be
judged, presented and used to steer the next iteration.

## Checks
- Which section of the paper does this iteration add to: Methods, Results, Discussion or
  Conclusions?
- What can be shown at the end of this iteration, in 3 to 4 days at most?
- Does that deliverable stand on its own, without the later phases?
- Which parts of the plan are time-consuming and not needed for the next deliverable? Move
  them to a later phase and say so.
- Which paths of this iteration can run at the same time? Is anything in a later iteration
  that needs no result of this one? If so, move it into this iteration.
- Is the number of iterations the smallest that the dependencies allow?
- If the estimate of an iteration is over a few days, what is the smaller version of it
  that still gives a conclusive result?
