# RiskShell Module Creation Guide

This document details the configuration options available when authoring a new declarative risk assessment module in RiskShell. 

For general information on how to run RiskShell, please refer back to the [README](README.md).

## Root Configuration Keys

When creating a new `.yaml` module, the following keys define the core metadata, logic, and output of your module. 

### Required Keys

| Key | Type | Description |
| :--- | :--- | :--- |
| `title` | String | The human-readable name of the risk assessment module. |
| `description` | String | A comprehensive summary explaining what the module models and its purpose. |
| `methodology` | String | A detailed breakdown of the mathematical or statistical approach utilised. |
| `pros` | List of Strings | Advantages or strengths of utilising this specific risk model. |
| `cons` | List of Strings | Limitations, weaknesses, or blind spots of the model. |
| `output_title` | String | The label printed next to the final calculated result (e.g., `"Calculated Risk Score:"`). |
| `variables` | List of Dicts | Definitions of the input parameters required to run the module (see [Variables Configuration](#variables-configuration) below). |

**Execution Logic (One of the following is required):**

| Key | Type | Description |
| :--- | :--- | :--- |
| `formula` | String | A mathematical string parsed safely by the engine (e.g., `"(ASSET_VALUE * EXPOSURE_FACTOR) * ARO"`). Ideal for static, deterministic algebra. |
| `script` | String | A raw Python block executed dynamically. Required if you need to use libraries like `numpy` for stochastic simulations (e.g., Monte Carlo). |

### Optional Keys

| Key | Type | Description |
| :--- | :--- | :--- |
| `output_prefix` | String | A string prepended to the final output value (e.g., `"£"` or `"$"`). |
| `output_postfix` | String | A string appended to the final output value (e.g., `"%"`). |

---

## Variables Configuration

The `variables` block is a list of dictionaries. Each dictionary defines a parameter that the user can set via the `set [var] [value]` command in the CLI.

| Key | Type | Description |
| :--- | :--- | :--- |
| `name` | String | **(Required)** The exact variable name used in the `formula` or `script`. |
| `default` | Float/Int | **(Required)** The fallback value used if the user does not supply one. |
| `required` | Boolean | **(Required)** Whether the user *must* set this value manually. If `true` and the default is null, the engine will block execution until set. |
| `description` | String | **(Required)** A clear explanation of what this variable represents. |
| `source` | String | **(Required)** The authoritative source for gathering this metric or a citable source used to derive the default value. |

---

## Graph Visualisation Configuration

RiskShell features a powerful ASCII rendering engine (`plotext`) for visualising heavy-tailed distributions and data points.

To enable graphing, append the `visualisation` block to your YAML schema.

### Core Visualisation Keys

| Key | Type | Description |
| :--- | :--- | :--- |
| `type` | String | **(Required)** The chart type. Supported options are: `histogram`, `scatter`, `plot`, and `bar`. |
| `data_variable` | String | **(Required for `histogram`)** The name of the list/array generated in your `script` containing the data to bin. |
| `x_variable` | String | **(Required for `scatter`, `plot`, `bar`)** The list/array defining the X-axis coordinates. |
| `y_variable` | String | **(Required for `scatter`, `plot`, `bar`)** The list/array defining the Y-axis coordinates. |

### Aesthetic Enhancements (Optional)

| Key | Type | Description |
| :--- | :--- | :--- |
| `title` | String | The title rendered above the graph. |
| `x_label` | String | The label printed below the X-axis. |
| `y_label` | String | The label printed alongside the Y-axis. |
| `height` | Integer | Constrains the vertical rows the graph will occupy (e.g., `20`). Highly recommended to prevent terminal scrolling. |
| `width` | Integer | Constrains the horizontal columns the graph will occupy. |
| `bins` | Integer | The number of buckets to divide data into (only applies to `histogram`). |
| `x_ticks` | Integer | Target number of ticks to render on the X-axis (dynamically calculates clean integer steps). |
| `y_ticks` | Integer | Target number of ticks to render on the Y-axis. |
| `colour` | String | The primary colour of the data markers. |
| `theme` | String | Built-in plotext theme to apply (e.g., `clear`, `pro`, `matrix`). |
| `grid` | Boolean | Set to `true` to render background crosshair grids, improving readability across wide terminals. |

---

## Viewport Boundaries Configuration

When graphing volatile data containing extreme outliers, linear auto-scaling algorithms can distort the graph or pad the lower boundaries into negative numbers. 

To resolve this, you can define a `visualisation_bounds` block at the root of the YAML to explicitly truncate the data payload and hard-clamp the rendering viewport.

| Key | Type | Description |
| :--- | :--- | :--- |
| `x_min_clamp` | Float/Int | Drops any data points below this value and strictly anchors the lowest edge of the X-axis viewport here (e.g., `0.0` to prevent negative visual boundaries). |
| `x_max_clamp` | Float/Int | Drops any data points above this value and anchors the maximum right edge of the X-axis viewport. |
| `x_max_percentile` | Float/Int | Dynamically calculates the given percentile (e.g., `99.0`) of your payload array and drops any long-tail outliers above it prior to rendering, preventing extreme horizontal distortion. |
