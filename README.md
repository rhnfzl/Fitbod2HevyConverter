# Fitbod2HevyConverter

Converts Fitbod workout CSV exports into the Strong CSV format that Hevy accepts for import.

## Usage

```bash
python converter.py <fitbod_export.csv> [output.csv]
```

**Example:**
```bash
python converter.py WorkoutExport_march2026.csv converted_for_hevy.csv
```

If no output filename is provided, the result is saved to `FitBodToHevyConvertedFile.csv`.

## How It Works

1. Reads a Fitbod CSV export (columns: Date, Exercise, Reps, Weight(kg), Duration(s), etc.)
2. Maps Fitbod exercise names to Hevy-compatible names (219 exercises mapped)
3. Outputs a semicolon-separated Strong CSV format that Hevy's import feature accepts

## Hevy Import

1. Run the converter to generate the output CSV
2. In Hevy, go to **Settings > Import Data**
3. Select the generated CSV file
4. Hevy will parse and import all workouts

## No Dependencies

Uses only the Python standard library (csv, sys, io). No pip install needed.
