# explore_dagster
Exploring Dagster. A distillation of a some key features taken primarily from Dagster documentation.

## Resources
- [documentation](https://docs.dagster.io/concepts)
- [experimental documentation notes](https://docs.dagster.io/master/_apidocs/experimental)
- ["Moving Past Airflow" article](https://dagster.io/blog/dagster-airflow)

## High-level overview of Dagster concepts

> Dagster is a data orchestrator. It lets you define pipelines (DAGs) in terms of the data flow between logical components called solids. These pipelines can be developed locally and run anywhere.

Dagster is a "data-aware" or "asset-aware" orchestrator.

### Building Blocks
The main building blocks of Dagster are the `Pipeline` and `Solid`. Note: Dagster is currently undergoing an API change based on user feedback for naming.
|Current API (v. 0.12) | Experimental API| Description |
| --- | --- | --- |
| Pipelines | Job (binding of Graph + resources) | "graphs of metadata-rich, parameterizable functions connected via data dependencies" |
| Solids | Op | function to "read inputs, perform an action, and emit outputs" |
| Composite Solids | -> Graphs | "unit of abstraction for composing a solid from other solids" |


#### Solids
- "Individual units of computations wired together to form a pipeline"
- All solids in a pipeline execute in same pipeline by default, but can be configured to run in separate processes (typical in production)
- Use decorator `@solid` for a function

#### Pipelines
- Set of solids arranged in a DAG
- Use decorator `@pipeline` for a function that calls solids
- When calling a solid inside a pipeline function, the function is not actually called - instead, the graph is built up


### Scheduler
Includes a scheduler, `dagster_daemon`, for managing different methods of launching pipeline runs:
- scheduled: fixed interval scheduling (beyond basic cron limitations, like considering holidays)
- sensors: external state changes (e.g. file appears in s3)
- queueing: priority queueing and max concurrent runs

### Web Interface
Dagster comes with a rich web interface called *Dagit* that allows you to inspect solids, pipelines, and assets produced by runs as well as launch pipelines, view run history, logs and more.

### Typing for rich metadata and validation
Dagster's type system is the secret sauce to the richer tooling and data-awareness.

Solids are enhanced by Dagster's **gradual** type system, which allows you to optionally describe what kinds of values the solids accept and produce. Dagit will perform type checks at runtime.
- When types are provided for input, the type check occurs immediately before the solid is executed.
- When types are provided for output, the type check occurs immediately after the solid is executed.

Dagster's types are defined in the `solid` decorator, as part of the input or output definitions.
|Current API (v. 0.12) | Experimental API| 
| --- | --- |
| `InputDefinition` | `In` |
| `OutputDefinition` | `Out` |

Dagster allows standard python type hints to coexist for static type checking.

The Dagit type system can provide rich behavior such as column-level schema validation on a Pandas dataframe using an including library `dagster-pandas`.

### Other Key Features

Dagster comes with [many libraries](https://github.com/dagster-io/dagster/tree/master/python_modules/libraries) for integration with aws, kubernetes, dask execution, pandas, pyspark, celery, and more.

Dagster attempts to make pipelines **testable** in an execution sense using a system of *modes* and *resources*. This allows testing for catching errors related to refactoring, graphs, configuration, syntax etc. A lot of data systems have logic in external systems (warehouses, etc.) - difficult to test in a 'lightweight' way. Dagster allows pipelines to define different modes (imagine "unit_test" and "prod") where the "unit_test" mode can be supplied with mocked resources. Dagster also allows for any subset execution of a pipeline.

Dagster provides **logging** features that any solid can emit messages to. Dagit provides a rich interface for filtering log messages. Stack traces are logged if errors are encountered.

Dagster provides `IOManager`s to allow the user to decide where outputs and inputs to solids should be stored, making it possible to separate data transformation logic from reading and writing results.

Dagster can run pipelines without long-running infrastructure requirements. Allows for simple local development and testing. Pipelines can be executed with python code, the CLI, or by starting a local Dagit server.

Dagster provides the concept of respositories, `RepositoryDefinition`, to organize a pipeline or group of pipelines in isolated processes. This means that the Dagster daemon and Dagit aren't affected by repository issues and each repository can have its own set of dependencies and python version. Separate process execution means that a bad pipeline won't bring down the orchestrator, and the orchestrator can be independently managed. Multiple repositories can be loaded together with the concept of a *workspace* (via creation of a `workspace.yaml`). 

The Dagster daemon can schedule *runs* (into processes, K8 jobs), which can in turn decide on their own task scheduling policy. This allows runs to be parallelized and optionally parallelize the tasks within the runs, if needed.