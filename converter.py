#!/usr/bin/env python
# coding: utf-8

"""Convert Fitbod CSV exports to Strong CSV format for Hevy import."""

import csv
import io
import sys
import time

from rapidfuzz import process, fuzz

# Exercise name mapping from Fitbod to official Hevy exercise names.
# Hevy names verified against hevy-gpt template IDs and hevyapp.com/exercises.
EXERCISE_MAPPING = {
    'Ab Crunch Machine': 'Crunch (Machine)',                              # hevy-gpt EB43ADD4
    'Air Squats': 'Squat (Bodyweight)',                                   # hevy-gpt 9694DA61
    'Arnold Dumbbell Press': 'Arnold Press (Dumbbell)',                   # hevy-gpt A69FF221
    'Assisted Chin Up': 'Chin Up (Assisted)',
    'Assisted Dip': 'Dip (Assisted)',
    'Assisted Neutral Grip Pull Up': 'Pull Up (Assisted)',
    'Assisted Pull Up': 'Pull Up (Assisted)',
    'Assisted Wide Grip Pull Up': 'Pull Up (Assisted)',
    'Australian Pull Up': 'Inverted Row',                                 # website confirmed
    'Back Extensions': 'Back Extension',
    'Back Squat': 'Squat (Barbell)',                                      # hevy-gpt D04AC939
    'Backward Arm Circle': 'Backward Arm Circle',
    'Barbell Bench Press': 'Bench Press (Barbell)',                       # hevy-gpt 79D0BB3A
    'Barbell Curl': 'Bicep Curl (Barbell)',                               # hevy-gpt A5AC6449
    'Barbell Hip Thrust': 'Hip Thrust (Barbell)',                         # hevy-gpt D57C2EC7
    'Barbell Incline Bench Press': 'Incline Bench Press (Barbell)',       # hevy-gpt 50DFDFAB
    'Barbell Lunge': 'Lunge (Barbell)',                                   # website confirmed
    'Barbell Shoulder Press': 'Overhead Press (Barbell)',                  # hevy-gpt 7B8D84E8
    'Barbell Shrug': 'Shrug (Barbell)',                                   # website confirmed
    'Bench Dip': 'Bench Dip',
    'Bench T-Spine Stretch': 'Bench T-Spine Stretch',
    'Bent Over Barbell Row': 'Bent Over Row (Barbell)',                   # hevy-gpt 55E6546F
    'Bicycle Crunch': 'Bicycle Crunch',
    'Bird Dog': 'Bird Dog',
    'Bodyweight Bulgarian Split Squat': 'Bulgarian Split Squat',
    'Burpee': 'Burpee',                                                  # hevy-gpt BB792A36
    'Cable Bicep Curl': 'Bicep Curl (Cable)',
    'Cable Crossover Fly': 'Cable Fly Crossovers',                       # hevy-gpt 651F844C
    'Cable Crunch': 'Cable Crunch',                                       # website confirmed
    'Cable Face Pull': 'Face Pull',                                       # website confirmed
    'Cable Hip Abduction': 'Hip Abduction (Cable)',
    'Cable Hip Adduction': 'Hip Adduction (Cable)',
    'Cable Lateral Raise': 'Lateral Raise (Cable)',
    'Cable One Arm Tricep Side Extension': 'Triceps Extension (Cable)',   # hevy-gpt 21310F5F
    'Cable One Arm Underhand Tricep Extension': 'Triceps Extension (Cable)',  # hevy-gpt 21310F5F
    'Cable Rear Delt Fly': 'Reverse Fly (Cable)',
    'Cable Rope Overhead Triceps Extension': 'Overhead Triceps Extension - Rope (Cable)',
    'Cable Rope Tricep Extension': 'Triceps Rope Pushdown',              # hevy-gpt 94B7239B
    'Cable Row': 'Seated Row (Cable)',
    'Cable Tricep Pushdown': 'Triceps Pushdown',                         # hevy-gpt 93A552C6
    'Cable Underhand Tricep Pushdown': 'Triceps Pushdown',               # hevy-gpt 93A552C6
    'Calf Press': 'Calf Press (Machine)',                                 # website confirmed
    'Cat Cow': 'Cat Cow',
    'Chest Expansion': 'Chest Expansion',
    'Chin Up': 'Chin Up',                                                 # hevy-gpt 29083183
    'Close-Grip Bench Press': 'Bench Press - Close Grip (Barbell)',       # website confirmed
    'Cross Body Hammer Curls': 'Cross Body Hammer Curl (Dumbbell)',
    'Crunches': 'Crunch',                                                 # hevy-gpt DCF3B31B
    'Cycling': 'Cycling',
    'Cycling - Stationary': 'Stationary Bike',
    'Dead Bug': 'Dead Bug',
    'Dead Hang': 'Dead Hang',                                             # website confirmed
    'Deadlift': 'Deadlift (Barbell)',                                     # hevy-gpt C6272009
    'Deadlift to Calf Raise': 'Deadlift (Barbell)',
    'Decline Crunch': 'Decline Crunch',                                   # hevy-gpt BC10A922
    'Decline Push Up': 'Decline Push Up',                                 # hevy-gpt C43825EA
    'Decline Russian Twists': 'Russian Twist',
    'Dip': 'Dip',
    'Diverging Seated Row': 'Seated Row (Machine)',                       # hevy-gpt 1DF4A847
    'Dumbbell Back Fly': 'Reverse Fly (Dumbbell)',
    'Dumbbell Bench Press': 'Bench Press (Dumbbell)',                     # hevy-gpt 3601968B
    'Dumbbell Bicep Curl': 'Bicep Curl (Dumbbell)',                       # hevy-gpt 37FCC2BB
    'Dumbbell Decline Bench Press': 'Decline Bench Press (Dumbbell)',     # hevy-gpt 18487FA7
    'Dumbbell Fly': 'Chest Fly (Dumbbell)',                               # hevy-gpt 12017185
    'Dumbbell Front Raise': 'Front Raise (Dumbbell)',
    'Dumbbell Goblet Squat': 'Goblet Squat',                             # hevy-gpt 3D0C7C75
    'Dumbbell Incline Bench Press': 'Incline Bench Press (Dumbbell)',     # hevy-gpt 07B38369
    'Dumbbell Incline Fly': 'Incline Chest Fly (Dumbbell)',               # hevy-gpt D3E2AB55
    'Dumbbell Kickbacks': 'Triceps Kickback (Dumbbell)',                  # hevy-gpt 6127A3AD
    'Dumbbell Lateral Raise': 'Lateral Raise (Dumbbell)',                 # hevy-gpt 422B08F1
    'Dumbbell Lunge': 'Lunge (Dumbbell)',                                 # hevy-gpt B537D09F
    'Dumbbell Pullover': 'Pullover (Dumbbell)',                           # website confirmed
    'Dumbbell Rear Delt Raise': 'Reverse Fly (Dumbbell)',
    'Dumbbell Romanian Deadlift': 'Romanian Deadlift (Dumbbell)',         # hevy-gpt 72CFFAD5
    'Dumbbell Row': 'Dumbbell Row',                                       # hevy-gpt F1E57334
    'Dumbbell Shoulder Press': 'Shoulder Press (Dumbbell)',               # hevy-gpt 878CD1D0
    'Dumbbell Shoulder Raise': 'Lateral Raise (Dumbbell)',
    'Dumbbell Shrug': 'Shrug (Dumbbell)',                                 # hevy-gpt ABEC557F
    'Dumbbell Skullcrusher': 'Skullcrusher (Dumbbell)',                   # hevy-gpt 68F8A292
    'Dumbbell Squat': 'Squat (Dumbbell)',
    'Dumbbell Squat To Shoulder Press': 'Thruster (Dumbbell)',
    'Dumbbell Superman': 'Superman',                                      # website confirmed
    'Dumbbell Tricep Extension': 'Triceps Extension (Dumbbell)',          # hevy-gpt 3765684D
    'Dumbbell Upright Row': 'Upright Row (Dumbbell)',
    'Dumbbell Walking Lunge': 'Walking Lunge (Dumbbell)',
    'EZ-Bar Curl': 'Bicep Curl (EZ Bar)',
    'EZ-Bar Overhead Tricep Extension': 'Overhead Triceps Extension (EZ Bar)',
    'EZ-Bar Reverse Grip Curl': 'Reverse Curl (EZ Bar)',
    'Elliptical': 'Elliptical Trainer',                                   # hevy-gpt 3303376C
    'Face Down Plate Neck Resistance': 'Neck Extension',
    "Farmer's Walk": "Farmer's Walk",                                     # website confirmed
    'Forward Arm Circle': 'Forward Arm Circle',
    'Forward Lunge with Twist': 'Lunge',                                  # hevy-gpt 5E1A7777
    'Front Squat': 'Front Squat',                                         # hevy-gpt 5046D0A9
    'Glute Kickback Machine': 'Glute Kickback (Machine)',                 # hevy-gpt CBA02382
    'Good Morning': 'Good Morning (Barbell)',                             # hevy-gpt 4180C405
    'Hack Squat': 'Hack Squat (Machine)',
    'Hammer Curls': 'Hammer Curl (Dumbbell)',                             # hevy-gpt 7E3BC8B6
    'Hammerstrength Chest Press': 'Chest Press (Machine)',                # hevy-gpt 7EB3F7C3
    'Hammerstrength Decline Chest Press': 'Decline Bench Press (Machine)',  # hevy-gpt FAF31231
    'Hammerstrength Incline Chest Press': 'Incline Chest Press (Machine)',  # hevy-gpt FBF92739
    'Hammerstrength Iso Row': 'Iso-Lateral Row (Machine)',                # hevy-gpt AA1EB7D8
    'Hammerstrength Shoulder Press': 'Seated Shoulder Press (Machine)',   # hevy-gpt 9237BAD1
    'Hanging Knee Raise': 'Hanging Knee Raise',                           # hevy-gpt 08590920
    'Hanging Leg Raise': 'Hanging Leg Raise',                             # hevy-gpt F8356514
    'Hiking': 'Hiking',
    'Hip Thrust': 'Hip Thrust (Barbell)',                                 # hevy-gpt D57C2EC7
    'Incline Back Extension': 'Back Extension',
    'Incline Dumbbell Curl': 'Incline Bicep Curl (Dumbbell)',
    'Incline Dumbbell Row': 'Incline Row (Dumbbell)',
    'Incline EZ-Bar Curl': 'Incline Bicep Curl (EZ Bar)',
    'Incline Hammer Curl': 'Incline Hammer Curl (Dumbbell)',
    'Inverted Row': 'Inverted Row',                                       # website confirmed
    "Kettlebell Single Arm Farmer Walk": "Farmer's Walk",                 # website confirmed
    'Kettlebell Swing': 'Kettlebell Swing',                               # hevy-gpt F8A0FCCA
    'Kettlebell Swing American': 'Kettlebell Swing',
    'Knee Up': 'Knee Raise Parallel Bars',                                # hevy-gpt 98237BA2
    'Lat Pulldown': 'Lat Pulldown (Cable)',                               # hevy-gpt 6A6C31A5
    'Leg Curl': 'Seated Leg Curl (Machine)',                              # hevy-gpt 11A123F3
    'Leg Extension': 'Leg Extension (Machine)',
    'Leg Press': 'Leg Press (Machine)',                                   # hevy-gpt C7973E0E
    'Leg Pull-In': 'Leg Pull In',
    'Leg Raise': 'Leg Raise',
    'Leg Swing': 'Leg Swing',
    'Lunge': 'Lunge',                                                     # hevy-gpt 5E1A7777
    'Lunge Twist': 'Lunge',                                              # hevy-gpt 5E1A7777
    'Lying Hamstrings Curl': 'Lying Leg Curl (Machine)',
    'Machine Bench Press': 'Chest Press (Machine)',                       # hevy-gpt 7EB3F7C3
    'Machine Bicep Curl': 'Bicep Curl (Machine)',
    'Machine Fly': 'Chest Fly (Machine)',                                 # hevy-gpt 78683336
    'Machine Hip Abductor': 'Hip Abduction (Machine)',                    # hevy-gpt F4B4C6EE
    'Machine Hip Adductor': 'Hip Adduction (Machine)',                    # hevy-gpt 8BEBFED6
    'Machine Leg Press': 'Leg Press (Machine)',                           # hevy-gpt C7973E0E
    'Machine Overhead Press': 'Seated Shoulder Press (Machine)',          # hevy-gpt 9237BAD1
    'Machine Preacher Curl': 'Preacher Curl (Machine)',
    'Machine Rear Delt Fly': 'Reverse Fly (Machine)',
    'Machine Reverse Fly': 'Reverse Fly (Machine)',
    'Machine Row': 'Seated Row (Machine)',                                # hevy-gpt 1DF4A847
    'Machine Shoulder Press': 'Seated Shoulder Press (Machine)',          # hevy-gpt 9237BAD1
    'Machine Tricep Dip': 'Triceps Dip (Machine)',
    'Machine Tricep Extension': 'Triceps Extension (Machine)',
    'Medicine Ball Russian Twist': 'Russian Twist',
    'Palms-Down Dumbbell Wrist Curl': 'Wrist Curl (Dumbbell)',
    'Palms-Up Dumbbell Wrist Curl': 'Wrist Curl (Dumbbell)',
    'Pendlay Row': 'Pendlay Row (Barbell)',                               # hevy-gpt 018ADC12
    'Plank': 'Plank',                                                     # hevy-gpt C6C9B8A0
    'Plank Shoulder Taps': 'Plank Shoulder Taps',
    'Preacher Curl': 'Preacher Curl (EZ Bar)',
    'Pull Up': 'Pull Up',                                                 # hevy-gpt 1B2B1E7C
    'Push Press': 'Push Press',                                           # website confirmed
    'Push Up': 'Push Up',                                                 # hevy-gpt 392887AA
    'PVC Around the World': 'PVC Around the World',
    'Reverse Barbell Curl': 'Reverse Curl (Barbell)',
    'Reverse Crunch': 'Reverse Crunch',
    'Reverse Dumbbell Curl': 'Reverse Curl (Dumbbell)',
    'Romanian Deadlift': 'Romanian Deadlift (Barbell)',                   # hevy-gpt 2B4B7310
    'Rowing': 'Rowing Machine',                                           # hevy-gpt 0222DB42
    'Running': 'Running',
    'Running - Treadmill': 'Treadmill',                                   # hevy-gpt 243710DE
    'Russian Twist': 'Russian Twist',
    'Scapular Pull Up': 'Scapular Pull Up',
    'Scissor Crossover Kick': 'Scissor Kicks',
    'Scissor Kick': 'Scissor Kicks',
    'Seated Back Extension': 'Back Extension (Machine)',                  # hevy-gpt A05C064D
    'Seated Cable Row': 'Seated Row (Cable)',
    'Seated Dumbbell Curl': 'Bicep Curl (Dumbbell)',                      # hevy-gpt 37FCC2BB
    'Seated Figure Four': 'Seated Figure Four',
    'Seated Leg Curl': 'Seated Leg Curl (Machine)',                       # hevy-gpt 11A123F3
    'Seated Machine Calf Press': 'Seated Calf Raise',                    # hevy-gpt 062AB91A
    'Seated Tricep Press': 'Overhead Triceps Extension (Machine)',
    'Side Bridge': 'Side Plank',
    'Single Arm Cable Bicep Curl': 'Bicep Curl (Cable)',
    'Single Arm Dumbbell Tricep Extension': 'Triceps Extension (Dumbbell)',  # hevy-gpt 3765684D
    'Single Arm Landmine Press': 'Landmine Press',
    'Single Leg Cable Kickback': 'Single Leg Cable Kickback',
    'Single Leg Glute Bridge': 'Single Leg Glute Bridge',                 # website confirmed
    'Single Leg Leg Extension': 'Leg Extension (Machine)',
    'Single Leg Overhead Kettlebell Hold': 'Single Leg Overhead Kettlebell Hold',
    'Single Leg Straight Forward Bend': 'Single Leg Straight Forward Bend',
    'Sit Up': 'Sit Up',                                                   # hevy-gpt 022DF610
    'Skullcrusher': 'Skullcrusher (Barbell)',                             # website confirmed
    'Sled Push': 'Sled Push',
    'Smith Machine Bench Press': 'Bench Press (Smith Machine)',
    'Smith Machine Calf Raise': 'Standing Calf Raise (Smith Machine)',
    'Smith Machine Incline Bench Press': 'Incline Bench Press (Smith Machine)',
    'Smith Machine Squat': 'Squat (Smith Machine)',
    'Spider Curls': 'Spider Curl (Dumbbell)',
    'Stability Ball Hip Bridge': 'Stability Ball Hip Bridge',
    'Stair Stepper': 'Stair Machine',
    'Standing Leg Side Hold': 'Standing Calf Raise',                      # hevy-gpt 06745E58
    'Standing Machine Calf Press': 'Standing Calf Raise',                # hevy-gpt 06745E58
    'Step Up': 'Step Up',
    'Stiff-Legged Barbell Good Morning': 'Good Morning (Barbell)',       # hevy-gpt 4180C405
    'Superman': 'Superman',                                               # website confirmed
    'Superman Hold': 'Superman',
    'Superman with Scaption': 'Superman',
    'T-Bar Row': 'T Bar Row',                                             # website confirmed
    'Toe Touchers': 'Toe Touchers',
    'Tricep Extension': 'Triceps Extension (Dumbbell)',                   # hevy-gpt 3765684D
    'Tricep Push Up': 'Diamond Push Up',                                  # website confirmed
    'Tricep Stretch': 'Tricep Stretch',
    'Upright Row': 'Upright Row (Barbell)',                               # website confirmed
    'V-Bar Pulldown': 'Lat Pulldown - V Bar (Cable)',
    'Vertical Knee Raise': 'Vertical Knee Raise',
    'Walking': 'Walking',
    'Walkout to Push Up': 'Walkout to Push Up',
    'Wide Grip Lat Pulldown': 'Lat Pulldown (Cable)',                     # hevy-gpt 6A6C31A5
    'Zottman Curl': 'Zottman Curl (Dumbbell)',                            # website confirmed
    'Zottman Preacher Curl': 'Zottman Preacher Curl (Dumbbell)',
}

# Official Hevy exercise names for fuzzy matching fallback.
# Combined from hevy-gpt (101 with template IDs), hevyapp.com/exercises, and community repos.
HEVY_EXERCISES = [
    # From hevy-gpt (official template IDs)
    'Arnold Press (Dumbbell)',
    'Back Extension (Machine)',
    'Bench Press (Barbell)',
    'Bench Press (Dumbbell)',
    'Bench Press - Close Grip (Barbell)',
    'Bench Press - Wide Grip (Barbell)',
    'Bent Over Row (Barbell)',
    'Bent Over Row (Dumbbell)',
    'Bicep Curl (Barbell)',
    'Bicep Curl (Cable)',
    'Bicep Curl (Dumbbell)',
    'Bicep Curl (Machine)',
    'Burpee',
    'Cable Crunch',
    'Cable Fly Crossovers',
    'Calf Extension (Machine)',
    'Calf Press (Machine)',
    'Chest Dip',
    'Chest Dip (Machine)',
    'Chest Dip (Weighted)',
    'Chest Fly (Dumbbell)',
    'Chest Fly (Machine)',
    'Chest Press (Machine)',
    'Chin Up',
    'Chin Up (Assisted)',
    'Concentration Curl',
    'Crunch',
    'Crunch (Machine)',
    'Deadlift (Barbell)',
    'Deadlift (Dumbbell)',
    'Decline Bench Press (Barbell)',
    'Decline Bench Press (Dumbbell)',
    'Decline Bench Press (Machine)',
    'Decline Crunch',
    'Decline Push Up',
    'Diamond Push Up',
    'Dip',
    'Dip (Assisted)',
    'Dumbbell Row',
    'Dumbbell Skullcrusher',
    'Elliptical Trainer',
    'Face Pull',
    "Farmer's Walk",
    'Front Squat',
    'Glute Bridge',
    'Glute Kickback (Machine)',
    'Glute Kickback on Floor',
    'Goblet Squat',
    'Good Morning (Barbell)',
    'Hack Squat (Machine)',
    'Hammer Curl (Cable)',
    'Hammer Curl (Dumbbell)',
    'Hanging Knee Raise',
    'Hanging Leg Raise',
    'Hip Abduction (Machine)',
    'Hip Adduction (Machine)',
    'Hip Thrust',
    'Hip Thrust (Barbell)',
    'Hip Thrust (Machine)',
    'Incline Bench Press (Barbell)',
    'Incline Bench Press (Dumbbell)',
    'Incline Chest Fly (Dumbbell)',
    'Incline Chest Press (Machine)',
    'Inverted Row',
    'Iso-Lateral Low Row',
    'Iso-Lateral Row (Machine)',
    'Jump Rope',
    'Jump Squat',
    'Jumping Jack',
    'Jumping Lunge',
    'Kettlebell Clean',
    'Kettlebell Curl',
    'Kettlebell Goblet Squat',
    'Kettlebell High Pull',
    'Kettlebell Shoulder Press',
    'Kettlebell Snatch',
    'Kettlebell Swing',
    'Kneeling Push Up',
    'Knee Raise Parallel Bars',
    'Lat Pulldown (Cable)',
    'Lat Pulldown (Machine)',
    'Lateral Raise (Cable)',
    'Lateral Raise (Dumbbell)',
    'Lateral Raise (Machine)',
    'Leg Extension (Machine)',
    'Leg Press (Machine)',
    'Leg Raise Parallel Bars',
    'Lunge',
    'Lunge (Barbell)',
    'Lunge (Dumbbell)',
    'Lying Leg Curl (Machine)',
    'Overhead Press (Barbell)',
    'Overhead Press (Dumbbell)',
    'Pendlay Row',
    'Pendlay Row (Barbell)',
    'Pike Pushup',
    'Plank',
    'Pull Up',
    'Pull Up (Assisted)',
    'Pullover (Dumbbell)',
    'Push Press',
    'Push Up',
    'Push Up (Weighted)',
    'Rack Pull',
    'Reverse Curl',
    'Reverse Lunge',
    'Romanian Deadlift (Barbell)',
    'Romanian Deadlift (Dumbbell)',
    'Rowing Machine',
    'Russian Twist',
    'Russian Twist (Bodyweight)',
    'Russian Twist (Weighted)',
    'Seated Calf Raise',
    'Seated Leg Curl (Machine)',
    'Seated Overhead Press (Barbell)',
    'Seated Overhead Press (Dumbbell)',
    'Seated Row (Machine)',
    'Seated Shoulder Press (Machine)',
    'Shoulder Press (Dumbbell)',
    'Shrug (Barbell)',
    'Shrug (Dumbbell)',
    'Single Leg Glute Bridge',
    'Single Leg Hip Thrust',
    'Sit Up',
    'Skullcrusher (Barbell)',
    'Skullcrusher (Dumbbell)',
    'Squat (Barbell)',
    'Squat (Bodyweight)',
    'Squat (Dumbbell)',
    'Standing Calf Raise',
    'Standing Military Press (Barbell)',
    'Stair Machine',
    'Stationary Bike',
    'Superman',
    'T Bar Row',
    'Treadmill',
    'Triceps Dip',
    'Triceps Dip (Machine)',
    'Triceps Dip (Weighted)',
    'Triceps Extension (Barbell)',
    'Triceps Extension (Cable)',
    'Triceps Extension (Dumbbell)',
    'Triceps Extension (Machine)',
    'Triceps Kickback (Dumbbell)',
    'Triceps Pushdown',
    'Triceps Rope Pushdown',
    'Upright Row (Barbell)',
    'Zottman Curl (Dumbbell)',
    # From website (additional confirmed exercises)
    'Around The World',
    'Back Extension',
    'Behind the Back Bicep Wrist Curl (Barbell)',
    'Bench Dip',
    'Bent Over Fly',
    'Bicycle Crunch',
    'Bird Dog',
    'Bulgarian Split Squat',
    'Cable Fly Crossovers',
    'Cat Cow',
    'Clean and Jerk',
    'Clean Pull',
    'Cycling',
    'Dead Bug',
    'Dead Hang',
    'Floor Press (Barbell)',
    'Flutter Kicks',
    'Front Raise (Dumbbell)',
    'Glute Ham Raise',
    'Goblet Squat',
    'Handstand Push Up',
    'Heel Taps',
    'Hiking',
    'Hollow Rock Hold',
    'Incline Bicep Curl (Dumbbell)',
    'Incline Push Ups',
    'Incline Row (Dumbbell)',
    'Kettlebell Turkish Get Up',
    'Kipping Pull Up',
    'Landmine Press',
    'Lateral Leg Raises',
    'Leg Pull In',
    'Leg Raise',
    'Lying Knee Raise',
    'Meadows Row',
    'Muscle Up',
    'Neck Extension',
    'Oblique Crunch',
    'One-Arm Push-Up',
    'One-Arm Tricep Extension (Dumbbell)',
    'Overhead Squat',
    'Plate Curls',
    'Plate Front Raise',
    'Plate Press',
    'Renegade Row',
    'Reverse Crunch',
    'Reverse Fly (Cable)',
    'Reverse Fly (Dumbbell)',
    'Reverse Fly (Machine)',
    'Reverse Plank',
    'Ring Dips',
    'Running',
    'Scapular Pull Up',
    'Scissor Kicks',
    'Side Plank',
    'Single Arm Lat Pulldown',
    'Single Leg Romanian Deadlift (Dumbbell)',
    'Sissy Squat',
    'Sled Push',
    'Spider Curl (Dumbbell)',
    'Split Squat (Dumbbell)',
    'Standing Leg Curls',
    'Step Up',
    'Sumo Deadlift',
    'Sumo Squat (Barbell)',
    'Thruster (Dumbbell)',
    'Thruster (Kettlebell)',
    'V Up',
    'Walking',
    'Wall Sit',
    'Wrist Curl (Dumbbell)',
]

# Strong CSV header (what Hevy accepts for import)
STRONG_CSV_HEADER = "Date;Workout Name;Exercise Name;Set Order;Weight;Weight Unit;Reps;RPE;Distance;Distance Unit;Seconds;Notes;Workout Notes;Workout Duration"


def fuzzy_match_exercise(fitbod_name, score_cutoff=75):
    """Find closest Hevy exercise for an unmapped Fitbod exercise via fuzzy matching."""
    result = process.extractOne(
        fitbod_name, HEVY_EXERCISES,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=score_cutoff
    )
    if result:
        matched_name, score, _ = result
        return matched_name, score
    return fitbod_name, 0


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
    fuzzy_matches = {}

    for row in rows:
        date_str = row['Date'].strip()
        exercise = row['Exercise'].strip()

        # Format date as ISO 8601 (first 19 chars: YYYY-MM-DDTHH:MM:SS)
        iso_date = date_str[:19].replace(' ', 'T', 1)

        # Workout name from date
        workout_name = f"Workout on: {date_str[:10]}"

        # Map exercise name: manual mapping first, then fuzzy match
        exercise_name = EXERCISE_MAPPING.get(exercise)
        if exercise_name is None:
            if exercise not in fuzzy_matches:
                matched, score = fuzzy_match_exercise(exercise)
                fuzzy_matches[exercise] = (matched, score)
            exercise_name = fuzzy_matches[exercise][0]

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

    # Report fuzzy matches
    if fuzzy_matches:
        print(f"\nFuzzy matched {len(fuzzy_matches)} unmapped exercise(s):")
        for fitbod_name, (hevy_name, score) in sorted(fuzzy_matches.items()):
            if score > 0:
                print(f"  '{fitbod_name}' -> '{hevy_name}' ({score:.0f}%)")
            else:
                print(f"  '{fitbod_name}' -> passed through (no match)")

    with open(output_file, 'w', newline='') as f:
        f.write('\n'.join(output_lines) + '\n')

    print(f"\nConverted {len(output_lines) - 1} sets -> {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python converter.py <fitbod_export.csv> [output.csv]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "FitBodToHevyConvertedFile.csv"
    convert_fitbod_to_hevy(input_file, output_file)
