#!/usr/bin/env python
# coding: utf-8

"""Convert Fitbod CSV exports to Strong CSV format for Hevy import."""

import csv
import io
import sys
import time

# Exercise name mapping from Fitbod to Hevy/Strong format
EXERCISE_MAPPING = {
    'Ab Crunch Machine': 'Crunch (Machine)',
    'Air Squats': 'Bodyweight Squat',
    'Arnold Dumbbell Press': 'Arnold Press (Dumbbell)',
    'Assisted Chin Up': 'Chin Up (Assisted)',
    'Assisted Dip': 'Dip (Assisted)',
    'Assisted Neutral Grip Pull Up': 'Pull Up (Assisted)',
    'Assisted Pull Up': 'Pull Up (Assisted)',
    'Assisted Wide Grip Pull Up': 'Pull Up (Assisted)',
    'Back Extensions': 'Back Extension',
    'Back Squat': 'Squat (Barbell)',
    'Backward Arm Circle': 'Backward Arm Circle',
    'Barbell Bench Press': 'Bench Press (Barbell)',
    'Barbell Curl': 'Bicep Curl (Barbell)',
    'Barbell Hip Thrust': 'Hip Thrust (Barbell)',
    'Barbell Incline Bench Press': 'Incline Bench Press (Barbell)',
    'Barbell Lunge': 'Lunge (Barbell)',
    'Barbell Shoulder Press': 'Overhead Press (Barbell)',
    'Barbell Shrug': 'Shrug (Barbell)',
    'Bench Dip': 'Bench Dip',
    'Bench T-Spine Stretch': 'Bench T-Spine Stretch',
    'Bent Over Barbell Row': 'Bent Over Row (Barbell)',
    'Bicycle Crunch': 'Bicycle Crunch',
    'Bird Dog': 'Bird Dog',
    'Bodyweight Bulgarian Split Squat': 'Bulgarian Split Squat',
    'Burpee': 'Burpee',
    'Cable Bicep Curl': 'Bicep Curl (Cable)',
    'Cable Crossover Fly': 'Cable Crossover',
    'Cable Crunch': 'Cable Crunch',
    'Cable Face Pull': 'Face Pull (Cable)',
    'Cable Hip Abduction': 'Hip Abduction (Cable)',
    'Cable Hip Adduction': 'Hip Adduction (Cable)',
    'Cable Lateral Raise': 'Lateral Raise (Cable)',
    'Cable One Arm Tricep Side Extension': 'Single Arm Triceps Pushdown (Cable)',
    'Cable One Arm Underhand Tricep Extension': 'Single Arm Triceps Pushdown (Cable)',
    'Cable Rear Delt Fly': 'Reverse Fly (Cable)',
    'Cable Rope Overhead Triceps Extension': 'Overhead Triceps Extension - Rope (Cable)',
    'Cable Rope Tricep Extension': 'Triceps Pushdown - Rope (Cable)',
    'Cable Row': 'Seated Row (Cable)',
    'Cable Tricep Pushdown': 'Triceps Pushdown (Cable)',
    'Cable Underhand Tricep Pushdown': 'Triceps Pushdown - Underhand (Cable)',
    'Calf Press': 'Calf Press (Machine)',
    'Cat Cow': 'Cat Cow',
    'Chest Expansion': 'Chest Expansion',
    'Chin Up': 'Chin Up',
    'Close-Grip Bench Press': 'Close Grip Bench Press (Barbell)',
    'Cross Body Hammer Curls': 'Cross Body Hammer Curl (Dumbbell)',
    'Crunches': 'Crunch',
    'Cycling': 'Cycling',
    'Cycling - Stationary': 'Stationary Bike',
    'Dead Bug': 'Dead Bug',
    'Dead Hang': 'Dead Hang',
    'Deadlift': 'Deadlift (Barbell)',
    'Deadlift to Calf Raise': 'Deadlift (Barbell)',
    'Decline Crunch': 'Decline Crunch',
    'Decline Push Up': 'Decline Push Up',
    'Decline Russian Twists': 'Russian Twist',
    'Dip': 'Dip',
    'Diverging Seated Row': 'Seated Row (Machine)',
    'Dumbbell Back Fly': 'Reverse Fly (Dumbbell)',
    'Dumbbell Bench Press': 'Bench Press (Dumbbell)',
    'Dumbbell Bicep Curl': 'Bicep Curl (Dumbbell)',
    'Dumbbell Decline Bench Press': 'Decline Bench Press (Dumbbell)',
    'Dumbbell Fly': 'Chest Fly (Dumbbell)',
    'Dumbbell Front Raise': 'Front Raise (Dumbbell)',
    'Dumbbell Goblet Squat': 'Goblet Squat (Dumbbell)',
    'Dumbbell Incline Bench Press': 'Incline Bench Press (Dumbbell)',
    'Dumbbell Incline Fly': 'Incline Chest Fly (Dumbbell)',
    'Dumbbell Kickbacks': 'Triceps Kickback (Dumbbell)',
    'Dumbbell Lateral Raise': 'Lateral Raise (Dumbbell)',
    'Dumbbell Lunge': 'Lunge (Dumbbell)',
    'Dumbbell Pullover': 'Pullover (Dumbbell)',
    'Dumbbell Rear Delt Raise': 'Reverse Fly (Dumbbell)',
    'Dumbbell Romanian Deadlift': 'Romanian Deadlift (Dumbbell)',
    'Dumbbell Row': 'Single Arm Row (Dumbbell)',
    'Dumbbell Shoulder Press': 'Shoulder Press (Dumbbell)',
    'Dumbbell Shoulder Raise': 'Lateral Raise (Dumbbell)',
    'Dumbbell Shrug': 'Shrug (Dumbbell)',
    'Dumbbell Skullcrusher': 'Lying Triceps Extension (Dumbbell)',
    'Dumbbell Squat': 'Squat (Dumbbell)',
    'Dumbbell Squat To Shoulder Press': 'Thruster (Dumbbell)',
    'Dumbbell Superman': 'Superman',
    'Dumbbell Tricep Extension': 'Triceps Extension (Dumbbell)',
    'Dumbbell Upright Row': 'Upright Row (Dumbbell)',
    'Dumbbell Walking Lunge': 'Walking Lunge (Dumbbell)',
    'EZ-Bar Curl': 'Bicep Curl (EZ Bar)',
    'EZ-Bar Overhead Tricep Extension': 'Overhead Triceps Extension (EZ Bar)',
    'EZ-Bar Reverse Grip Curl': 'Reverse Curl (EZ Bar)',
    'Elliptical': 'Elliptical',
    'Face Down Plate Neck Resistance': 'Neck Extension',
    "Farmer's Walk": 'Farmers Walk',
    'Forward Arm Circle': 'Forward Arm Circle',
    'Forward Lunge with Twist': 'Lunge (Bodyweight)',
    'Front Squat': 'Front Squat (Barbell)',
    'Glute Kickback Machine': 'Glute Kickback (Machine)',
    'Good Morning': 'Good Morning (Barbell)',
    'Hack Squat': 'Hack Squat (Machine)',
    'Hammer Curls': 'Hammer Curl (Dumbbell)',
    'Hammerstrength Chest Press': 'Chest Press (Machine)',
    'Hammerstrength Decline Chest Press': 'Decline Chest Press (Machine)',
    'Hammerstrength Incline Chest Press': 'Incline Chest Press (Machine)',
    'Hammerstrength Iso Row': 'Machine Row',
    'Hammerstrength Shoulder Press': 'Shoulder Press (Machine)',
    'Hanging Knee Raise': 'Hanging Knee Raise',
    'Hanging Leg Raise': 'Hanging Leg Raise',
    'Hiking': 'Hiking',
    'Hip Thrust': 'Hip Thrust (Barbell)',
    'Incline Back Extension': 'Back Extension',
    'Incline Dumbbell Curl': 'Incline Bicep Curl (Dumbbell)',
    'Incline Dumbbell Row': 'Incline Row (Dumbbell)',
    'Incline EZ-Bar Curl': 'Incline Bicep Curl (EZ Bar)',
    'Incline Hammer Curl': 'Incline Hammer Curl (Dumbbell)',
    'Inverted Row': 'Inverted Row',
    'Kettlebell Single Arm Farmer Walk': 'Farmers Walk',
    'Kettlebell Swing': 'Kettlebell Swing',
    'Kettlebell Swing American': 'Kettlebell Swing',
    'Lat Pulldown': 'Lat Pulldown (Cable)',
    'Leg Curl': 'Seated Leg Curl (Machine)',
    'Leg Extension': 'Leg Extension (Machine)',
    'Leg Press': 'Leg Press (Machine)',
    'Leg Pull-In': 'Leg Pull In',
    'Leg Raise': 'Leg Raise',
    'Leg Swing': 'Leg Swing',
    'Lunge': 'Lunge (Bodyweight)',
    'Lunge Twist': 'Lunge (Bodyweight)',
    'Lying Hamstrings Curl': 'Lying Leg Curl (Machine)',
    'Machine Bench Press': 'Chest Press (Machine)',
    'Machine Bicep Curl': 'Bicep Curl (Machine)',
    'Machine Fly': 'Chest Fly (Machine)',
    'Machine Hip Abductor': 'Hip Abduction (Machine)',
    'Machine Hip Adductor': 'Hip Adduction (Machine)',
    'Machine Leg Press': 'Leg Press (Machine)',
    'Machine Overhead Press': 'Shoulder Press (Machine)',
    'Machine Preacher Curl': 'Preacher Curl (Machine)',
    'Machine Rear Delt Fly': 'Reverse Fly (Machine)',
    'Machine Reverse Fly': 'Reverse Fly (Machine)',
    'Machine Row': 'Machine Row',
    'Machine Shoulder Press': 'Shoulder Press (Machine)',
    'Machine Tricep Dip': 'Triceps Dip (Machine)',
    'Machine Tricep Extension': 'Triceps Extension (Machine)',
    'Medicine Ball Russian Twist': 'Russian Twist',
    'Palms-Down Dumbbell Wrist Curl': 'Wrist Curl (Dumbbell)',
    'Palms-Up Dumbbell Wrist Curl': 'Wrist Curl (Dumbbell)',
    'Pendlay Row': 'Pendlay Row (Barbell)',
    'Plank': 'Plank',
    'Plank Shoulder Taps': 'Plank Shoulder Taps',
    'Preacher Curl': 'Preacher Curl (EZ Bar)',
    'Pull Up': 'Pull Up',
    'Push Press': 'Push Press (Barbell)',
    'Push Up': 'Push Up',
    'PVC Around the World': 'PVC Around the World',
    'Reverse Barbell Curl': 'Reverse Curl (Barbell)',
    'Reverse Crunch': 'Reverse Crunch',
    'Reverse Dumbbell Curl': 'Reverse Curl (Dumbbell)',
    'Romanian Deadlift': 'Romanian Deadlift (Barbell)',
    'Rowing': 'Rowing Machine',
    'Running': 'Running',
    'Running - Treadmill': 'Treadmill',
    'Russian Twist': 'Russian Twist',
    'Scapular Pull Up': 'Scapular Pull Up',
    'Scissor Crossover Kick': 'Scissor Kicks',
    'Scissor Kick': 'Scissor Kicks',
    'Seated Back Extension': 'Back Extension (Machine)',
    'Seated Dumbbell Curl': 'Bicep Curl (Dumbbell)',
    'Seated Figure Four': 'Seated Figure Four',
    'Seated Leg Curl': 'Seated Leg Curl (Machine)',
    'Seated Machine Calf Press': 'Seated Calf Raise (Machine)',
    'Seated Tricep Press': 'Overhead Triceps Extension (Machine)',
    'Side Bridge': 'Side Plank',
    'Single Arm Cable Bicep Curl': 'Bicep Curl (Cable)',
    'Single Arm Dumbbell Tricep Extension': 'Triceps Extension (Dumbbell)',
    'Single Arm Landmine Press': 'Landmine Press',
    'Single Leg Cable Kickback': 'Single Leg Cable Kickback',
    'Single Leg Glute Bridge': 'Single Leg Glute Bridge',
    'Single Leg Leg Extension': 'Leg Extension (Machine)',
    'Single Leg Overhead Kettlebell Hold': 'Single Leg Overhead Kettlebell Hold',
    'Single Leg Straight Forward Bend': 'Single Leg Straight Forward Bend',
    'Sit Up': 'Sit Up',
    'Skullcrusher': 'Lying Triceps Extension (EZ Bar)',
    'Sled Push': 'Sled Push',
    'Smith Machine Bench Press': 'Bench Press (Smith Machine)',
    'Smith Machine Calf Raise': 'Standing Calf Raise (Smith Machine)',
    'Smith Machine Incline Bench Press': 'Incline Bench Press (Smith Machine)',
    'Smith Machine Squat': 'Squat (Smith Machine)',
    'Spider Curls': 'Spider Curl (Dumbbell)',
    'Stability Ball Hip Bridge': 'Stability Ball Hip Bridge',
    'Stair Stepper': 'Stair Machine',
    'Standing Leg Side Hold': 'Standing Calf Raise',
    'Standing Machine Calf Press': 'Standing Calf Raise (Machine)',
    'Step Up': 'Step Up',
    'Stiff-Legged Barbell Good Morning': 'Good Morning (Barbell)',
    'Superman': 'Superman',
    'Superman Hold': 'Superman',
    'Superman with Scaption': 'Superman',
    'T-Bar Row': 'T Bar Row',
    'Toe Touchers': 'Toe Touchers',
    'Tricep Extension': 'Triceps Extension (Dumbbell)',
    'Tricep Push Up': 'Diamond Push Up',
    'Tricep Stretch': 'Tricep Stretch',
    'Upright Row': 'Upright Row (Barbell)',
    'V-Bar Pulldown': 'Lat Pulldown - V Bar (Cable)',
    'Vertical Knee Raise': 'Vertical Knee Raise',
    'Walking': 'Walking',
    'Walkout to Push Up': 'Walkout to Push Up',
    'Wide Grip Lat Pulldown': 'Lat Pulldown (Cable)',
    'Zottman Curl': 'Zottman Curl (Dumbbell)',
    'Zottman Preacher Curl': 'Zottman Preacher Curl (Dumbbell)',
}

# Strong CSV header (what Hevy accepts for import)
STRONG_CSV_HEADER = "Date;Workout Name;Exercise Name;Set Order;Weight;Weight Unit;Reps;RPE;Distance;Distance Unit;Seconds;Notes;Workout Notes;Workout Duration"


def parse_csv_data(file_path):
    """Parse Fitbod CSV export file."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    content = content.replace('\r\n', '\n').replace('\r', '\n')
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    for row in reader:
        exercise = (row.get('Exercise') or '').strip()
        date = (row.get('Date') or '').strip()
        if exercise and date:
            rows.append(row)
    return rows


def convert_fitbod_to_hevy(input_file, output_file="FitBodToHevyConvertedFile.csv"):
    """Convert Fitbod CSV export to Strong CSV format for Hevy import."""
    print(f"Reading {input_file}...")
    rows = parse_csv_data(input_file)
    print(f"Found {len(rows)} exercise sets")

    if not rows:
        print("No valid data found!")
        return

    set_order_tracker = {}
    output_lines = [STRONG_CSV_HEADER]

    for row in rows:
        date_str = row['Date'].strip()
        exercise = row['Exercise'].strip()

        # Format date as ISO 8601 (first 19 chars: YYYY-MM-DDTHH:MM:SS)
        iso_date = date_str[:19].replace(' ', 'T', 1)

        # Workout name from date
        workout_name = f"Workout on: {date_str[:10]}"

        # Map exercise name
        exercise_name = EXERCISE_MAPPING.get(exercise, exercise)

        # Track set order per (date, exercise) pair, 1-indexed
        set_key = f"{date_str[:10]}_{exercise}"
        if set_key not in set_order_tracker:
            set_order_tracker[set_key] = 1
        set_order = set_order_tracker[set_key]
        set_order_tracker[set_key] += 1

        # Weight in kg, apply multiplier
        weight_kg = float(row.get('Weight(kg)', '0').strip() or '0')
        multiplier = float(row.get('multiplier', '1').strip() or '1')
        weight = round(weight_kg * multiplier, 2)

        # Reps
        reps_str = (row.get('Reps') or '0').strip()
        reps_val = int(float(reps_str)) if reps_str else 0
        reps = str(reps_val) if reps_val > 0 else ''

        # Duration in seconds
        duration_str = (row.get('Duration(s)') or '0').strip()
        duration = int(float(duration_str)) if duration_str else 0
        seconds = str(duration) if duration > 0 else '0'

        # Build semicolon-separated row
        fields = [
            iso_date,           # Date
            workout_name,       # Workout Name
            exercise_name,      # Exercise Name
            str(set_order),     # Set Order
            str(weight),        # Weight
            'kg',               # Weight Unit
            reps,               # Reps
            '',                 # RPE
            '',                 # Distance
            '',                 # Distance Unit
            seconds,            # Seconds
            '',                 # Notes
            '',                 # Workout Notes
            '60m',              # Workout Duration
        ]
        output_lines.append(';'.join(fields))

    with open(output_file, 'w', newline='') as f:
        f.write('\n'.join(output_lines) + '\n')

    print(f"Converted {len(output_lines) - 1} sets -> {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python converter.py <fitbod_export.csv> [output.csv]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "FitBodToHevyConvertedFile.csv"
    convert_fitbod_to_hevy(input_file, output_file)
