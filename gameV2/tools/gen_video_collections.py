#!/usr/bin/env python3
"""Generate the VIDEO_COLLECTIONS JS literal for index.html.

Reads the real WebP filenames from gameV2/videoAssets/<Folder>/ (so the `img`
strings match disk byte-for-byte, curly apostrophes and colons included) and
pairs each file with its title (alt text) + YouTube URL transcribed from
"Video Link List.pdf". Matching is by fuzzy similarity within each folder, so
the on-disk name and the PDF title don't have to be identical.

Each row also carries the image's intrinsic w/h. buildPhotoGrid() puts those on
the <img> so the grid reserves the right box BEFORE the file arrives — without
them the cell is zero-height under `width:100%; height:auto`, and the float
animation, which measures getBoundingClientRect() 600ms after opening, starts
from collapsed rects and the grid jumps as images land.

Thumbnails are produced by prep_video_thumbs.py; run that first if you have
dropped in fresh PNG exports.

Run:  python3 gameV2/tools/gen_video_collections.py
Paste the printed block into index.html where VIDEO_COLLECTIONS is defined.
"""
import os, json, difflib

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'videoAssets'))

# folder -> [(title/alt, url), ...] straight from the PDF.
PDF = {
    'Games': [
        ('Making a Slip n Slide Section', 'https://www.youtube.com/watch?v=VW5gHMxPqmA&list=PLf2smdNBnoCoHGkCuEk11hdysNYUcJ8XS&index=17'),
        ('Seabeck Slip n Slide aka Slip n Flip', 'https://www.youtube.com/watch?v=5Nr-45lweZc&list=PLf2smdNBnoCoHGkCuEk11hdysNYUcJ8XS&index=24'),
        ('Giant Jenga Record Skola', 'https://www.youtube.com/watch?v=USWvMcyrHmI&list=PLf2smdNBnoCoHGkCuEk11hdysNYUcJ8XS&index=26'),
        ('Milton’s Crackers with a Giant Jenga Back', 'https://www.youtube.com/watch?v=cT9V1UM00Hw&list=PLf2smdNBnoCoHGkCuEk11hdysNYUcJ8XS&index=29'),
        ('HOW TO MAKE A MAZE', 'https://www.youtube.com/watch?v=_oskFS8g-jA&list=PLf2smdNBnoCoHGkCuEk11hdysNYUcJ8XS&index=32'),
    ],
    'Rojo': [
        ('Dr. Green Is In The Building', 'https://www.youtube.com/watch?v=wQRdbgNREXs&list=PLf2smdNBnoCpOjXsUXkVSb86xNLm5AU4X'),
        ('Los Coco Nuts', 'https://www.youtube.com/watch?v=z3ALVqS4vqI&list=PLf2smdNBnoCpOjXsUXkVSb86xNLm5AU4X&index=3'),
        ('Pescado Adventure and Fish Feed Fiesta Mazatlan and PANCHOS', 'https://www.youtube.com/watch?v=1PjmfQ-SrRA&list=PLf2smdNBnoCpOjXsUXkVSb86xNLm5AU4X&index=6'),
    ],
    'Nonprofits': [
        ('The Skola Brogan Finds His Place', 'https://www.youtube.com/watch?v=Im1kP1Tm4MI&list=PLf2smdNBnoCrXnfjsWv7FyXgn3gWFsYED&index=9'),
        ('Farm Dinner - Trailer', 'https://www.youtube.com/watch?v=mClZcX7LRmI&list=PLf2smdNBnoCrXnfjsWv7FyXgn3gWFsYED&index=18'),
        ('Dream Biking Glacier #2', 'https://www.youtube.com/watch?v=fpYaRCR7Kek&list=PLf2smdNBnoCrXnfjsWv7FyXgn3gWFsYED&index=19'),
        ('Lion’s Club Garden - KILLER SQUASH', 'https://www.youtube.com/watch?v=9w7IX9AyQ0Q&list=PLf2smdNBnoCrXnfjsWv7FyXgn3gWFsYED&index=12'),
    ],
    'Make A Joyful Noise': [
        ('makeajoyfulnoise', 'https://www.youtube.com/watch?v=cDQF908GoI4&list=PLf2smdNBnoCp5SjSjDusqiX0dKWRGMWHq'),
        ('Gongs Seattle Go MOBILE 5/3/20', 'https://www.youtube.com/watch?v=NLYF6NmZkt4&list=PLf2smdNBnoCp5SjSjDusqiX0dKWRGMWHq&index=7'),
        ('Chaos Gongland', 'https://www.youtube.com/watch?v=V8iP-ksGyoY&list=PLf2smdNBnoCp5SjSjDusqiX0dKWRGMWHq&index=11'),
        ('Gongs Seattle 4/30/20', 'https://www.youtube.com/watch?v=cR9e59bCjZc&list=PLf2smdNBnoCp5SjSjDusqiX0dKWRGMWHq&index=25'),
        ('Gongs Seattle #MakeAJoyfulNoise pizza? 5/2/20', 'https://www.youtube.com/watch?v=JED7xeuAJBA&list=PLf2smdNBnoCp5SjSjDusqiX0dKWRGMWHq&index=27'),
    ],
    'Nick At Home': [
        ('Nick At Home P= P Trap', 'https://www.youtube.com/watch?v=8Rte23GoAkI&list=PLf2smdNBnoCrAlwQwQ1nfEoIkrJEPm2UR'),
        ('Nick At Home A-Z A = Series Setup', 'https://www.youtube.com/watch?v=VVPrmGOXV6M&list=PLf2smdNBnoCrAlwQwQ1nfEoIkrJEPm2UR&index=4'),
        ('Erratic Appears Zentner\'s Yard', 'https://www.youtube.com/watch?v=vR83RRQHgu8&list=PLf2smdNBnoCrAlwQwQ1nfEoIkrJEPm2UR&index=12'),
        ('What Did He Say?', 'https://www.youtube.com/watch?v=6xx65hVIqVs&list=PLf2smdNBnoCrAlwQwQ1nfEoIkrJEPm2UR&index=7'),
    ],
    'Mom My Straightman': [
        ('Mom finally loads our firewood at Chelan', 'https://www.youtube.com/watch?v=LAQtZIre2Zc&list=PLf2smdNBnoCoywrAS47-ZwPZYBWIMGRqQ'),
        ('Now get to work mom', 'https://www.youtube.com/watch?v=25J3XGsJils&list=PLf2smdNBnoCoywrAS47-ZwPZYBWIMGRqQ&index=3'),
        ('Hard to get good movers for your good stuff.....thanks mom', 'https://www.youtube.com/watch?v=j3S6GbUH5HU&list=PLf2smdNBnoCoywrAS47-ZwPZYBWIMGRqQ&index=4'),
        ('Old Lady Boogie Boards Mazatlan 2014', 'https://www.youtube.com/watch?v=NWnfZHkM67Q&list=PLf2smdNBnoCoywrAS47-ZwPZYBWIMGRqQ&index=7'),
    ],
    'Stay Home Safe Secure': [
        ('Stay Home Safe Secure Tip #15 Get Car Protected', 'https://www.youtube.com/watch?v=GCPzlhNKsvE&list=PLf2smdNBnoCo9Jp3vn3RyBq8LoMrUcjGB&index=18'),
        ('Stay Home Safe Secure Tip # 44 Home Haircuts By Mr. Chew', 'https://www.youtube.com/watch?v=PFZ5O5sNx_Q&list=PLf2smdNBnoCo9Jp3vn3RyBq8LoMrUcjGB&index=8'),
        ('GIANT BALL FOR PIZZA', 'https://www.youtube.com/watch?v=FZ_yGqdsjgc&list=PLf2smdNBnoCo9Jp3vn3RyBq8LoMrUcjGB&index=27'),
        ('Stay Home Safe Secure Tip #12 Rolling Clean System', 'https://www.youtube.com/watch?v=Rwqdywv2otw&list=PLf2smdNBnoCo9Jp3vn3RyBq8LoMrUcjGB&index=29'),
        ('Power Twenty Concept 2 Rowing #23 Tip in Stay Home Safe Secure series.', 'https://www.youtube.com/watch?v=Vzlc9K7hEQA&list=PLf2smdNBnoCo9Jp3vn3RyBq8LoMrUcjGB&index=27'),
        ('Stay Home Safe Secure Tip #44.c Back for a Free Tinge', 'https://www.youtube.com/watch?v=Uj2qgjDGjaQ&list=PLf2smdNBnoCo9Jp3vn3RyBq8LoMrUcjGB&index=29'),
    ],
    'Orange Man Adventure Theatre': [
        ('OrangeMan Ski Bump', 'https://www.youtube.com/watch?v=XWE-vUIZLhs&list=PLf2smdNBnoCq2Uj7jkL-cfmdRVx5dcmcp&index=2'),
        ('OrangeMan on Owyhee River...¿Which Way?', 'https://www.youtube.com/watch?v=dHvg6N9PbCc&list=PLf2smdNBnoCq2Uj7jkL-cfmdRVx5dcmcp&index=5'),
        ('OrangeMan in Antarctica', 'https://www.youtube.com/watch?v=xv4UijG8pnw&list=PLf2smdNBnoCq2Uj7jkL-cfmdRVx5dcmcp&index=8'),
        ('OrangeMan Loves That’s Amore', 'https://www.youtube.com/watch?v=UaisA6Nfw-U&list=PLf2smdNBnoCq2Uj7jkL-cfmdRVx5dcmcp&index=10'),
        ('Go for Pizza Safely', 'https://www.youtube.com/watch?v=Kdf-JvAa96U&list=PLf2smdNBnoCq2Uj7jkL-cfmdRVx5dcmcp&index=13'),
    ],
    'Just Borg': [
        ('Christmas Self Sabotage Deflated', 'https://www.youtube.com/watch?v=B3752r5NIfY&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=10'),
        ('I thought it was TEFLON 2', 'https://www.youtube.com/watch?v=L7p-gXjWJQ0&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=12'),
        ('House Sitting HIRE or FIRE ?', 'https://www.youtube.com/watch?v=zcbTzu8C4j4&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=13'),
        ('Feeding Tube - Taking Tequila Cleanse', 'https://www.youtube.com/watch?v=yI4zXbZhHs4&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=15'),
        ('Pizza Night at Brog’s experimental kitchen', 'https://www.youtube.com/watch?v=ZOJzkTGJ3K0&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=21'),
        ('Nightmare Haircut', 'https://www.youtube.com/watch?v=-I56YHLQA5g&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=22'),
        ('Cinder Cone Popcorn Visual', 'https://www.youtube.com/watch?v=zgTvX-o2_mM&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=28'),
        ('Almost A Cleaning by Dr. Disinfectant', 'https://www.youtube.com/watch?v=mAh30Zy6ZLU&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=26'),
        ('I got to Hand it to ya.', 'https://www.youtube.com/watch?v=dILBWPSul9g&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=31'),
        ('How to tie a SAFETY ROPE on a ladder.', 'https://www.youtube.com/watch?v=BHnIekV4k3E&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=41'),
        ('Light Buddy 2012', 'https://www.youtube.com/watch?v=elvv58M3P3I&list=PLf2smdNBnoCoRBV_pOlq9-6lacaXh_qiB&index=45'),
    ],
    'Trailers': [
        ('The Storage Wars Trailer 1', 'https://www.youtube.com/watch?v=SZrI0KG2hag&list=PLf2smdNBnoCosJa7pSsQMEZrml9hqcrd6&index=2'),
        ('Judkins Food Review Teaser....food fun over the last couple weeks.. Yum', 'https://www.youtube.com/watch?v=lZf7Xwsjdr8&list=PLf2smdNBnoCosJa7pSsQMEZrml9hqcrd6&index=28'),
        ('Vote Mail Is Easy just the Trailer', 'https://www.youtube.com/watch?v=L0Y23uvPZ5M&list=PLf2smdNBnoCosJa7pSsQMEZrml9hqcrd6&index=13'),
        ('The Perfect Stone', 'https://www.youtube.com/watch?v=WhZFpArFxXI&list=PLf2smdNBnoCosJa7pSsQMEZrml9hqcrd6&index=14'),
        ('Disinfectant WARS - just the Trailer', 'https://www.youtube.com/watch?v=UOVRQff4ePg&list=PLf2smdNBnoCosJa7pSsQMEZrml9hqcrd6&index=15'),
        ('Almost A Cleaning', 'https://www.youtube.com/watch?v=Vf78VDnaEx0&list=PLf2smdNBnoCosJa7pSsQMEZrml9hqcrd6&index=27'),
    ],
    'Vote Mail Is Easy': [
        ('VOTE MAIL IS EASY-By Kayak', 'https://www.youtube.com/watch?v=P7L8UXWfs3I&list=PLf2smdNBnoCrPoHTrT9mBejcBuEv624b9&index=2'),
        ('VOTE MAIL IS EASY-VOTE BY BUS STOP', 'https://www.youtube.com/watch?v=iaFv2Mk41Bc&list=PLf2smdNBnoCrPoHTrT9mBejcBuEv624b9&index=5'),
        ('VOTE MAIL IS EASY- Skyline Airmail (captions)', 'https://www.youtube.com/watch?v=CWerLOHCK-A&list=PLf2smdNBnoCrPoHTrT9mBejcBuEv624b9&index=8'),
        ('VOTE MAIL IS EASY- Sitting on Break', 'https://www.youtube.com/watch?v=CJ4uMDTk0dQ&list=PLf2smdNBnoCrPoHTrT9mBejcBuEv624b9&index=9'),
        ('VOTE MAIL IS EASY-In The Alley', 'https://www.youtube.com/watch?v=0arCw1azCxY&list=PLf2smdNBnoCrPoHTrT9mBejcBuEv624b9&index=11'),
    ],
}


def norm(s):
    return ''.join(ch.lower() for ch in s if ch.isalnum())


def match_folder(folder, entries):
    files = sorted(f for f in os.listdir(os.path.join(ASSETS, folder)) if f.lower().endswith('.webp'))
    # Build a score matrix, then greedily take the best file<->entry pair each round.
    pairs = []
    for fi, f in enumerate(files):
        for ei, (title, url) in enumerate(entries):
            score = difflib.SequenceMatcher(None, norm(f), norm(title)).ratio()
            pairs.append((score, fi, ei))
    pairs.sort(reverse=True)
    used_f, used_e, out = set(), set(), {}
    for score, fi, ei in pairs:
        if fi in used_f or ei in used_e:
            continue
        used_f.add(fi); used_e.add(ei)
        out[fi] = (files[fi], entries[ei][0], entries[ei][1], score)
    return [out[i] for i in range(len(files))], files, entries


def main():
    lines = ['const VIDEO_COLLECTIONS = {']
    warnings = []
    for folder in PDF:
        matched, files, entries = match_folder(folder, PDF[folder])
        if len(files) != len(entries):
            warnings.append(f'  COUNT MISMATCH {folder}: {len(files)} files vs {len(entries)} PDF entries')
        lines.append(f'  {json.dumps(folder)}: [')
        for fname, title, url, score in matched:
            if score < 0.5:
                warnings.append(f'  LOW MATCH ({score:.2f}) {folder}: "{fname}" -> "{title}"')
            w, h = Image.open(os.path.join(ASSETS, folder, fname)).size
            lines.append(f'    {{ img: {json.dumps(fname, ensure_ascii=False)}, alt: {json.dumps(title, ensure_ascii=False)}, '
                         f'w: {w}, h: {h}, url: {json.dumps(url)} }},')
        lines.append('  ],')
    lines.append('};')
    print('\n'.join(lines))
    if warnings:
        import sys
        print('\n// ---- review these matches ----', file=sys.stderr)
        for w in warnings:
            print('//' + w, file=sys.stderr)


if __name__ == '__main__':
    main()
