checkbox_map = {
    "1": "Head",
    "2": "Abdomen",
    "3": "Elbow",
    "4": "Hip",
    "5": "Lower leg (incl. Achilles tendon)",
    "6": "Neck",
    "7": "Lumbosacral",
    "8": "Forearm",
    "9": "Groin",
    "10": "Ankle",
    "11": "Chest",
    "12": "Shoulder",
    "13": "Wrist",
    "14": "Thigh",
    "15": "Foot",
    "16": "Thoracic spine",
    "17": "Upper arm",
    "18": "Hand",
    "19": "Knee",
    "20": "Right",
    "21": "Left",
    "22": "Bilateral/central",
    "23": "Concussion",
    "24": "Meniscus lesion",
    "25": "Haematoma/contusion/bruise (incl. compartment syndrome)",
    "26": "Fracture (specify if stress fracture)",
    "27": "Cartilage lesion",
    "28": "Nerve injury (central or peripheral other than concussion)",
    "29": "Other bone injury (e.g., bone stress)",
    "30": "Muscle rupture/tear/strain**",
    "31": "Dental injury*",
    "32": "Joint dislocation/subluxation*",
    "33": "Tendon rupture/tendinopathy",
    "34": "Vessel injury (excl. skin haematoma)",
    "35": "Joint sprain (i.e., ligament/capsule)",
    "36": "Abrasion",
    "37": "Bursitis",
    "38": "Arthritis/synovitis/capsulitis",
    "39": "Laceration",
    "40": "Overuse unspecified",
    "41": "Other injury (please specify):",
    "42": "Training",
    "43": "Match (min. of injury)",
    "44": "N/A (gradual onset injury)",
    "45": "Football training",
    "46": "Football & other training",
    "47": "League match",
    "48": "Friendly match",
    "49": "Other training",
    "50": "Reserve/youth team training",
    "51": "Champions League",
    "52": "Reserve/youth team match",
    "53": "National team",
    "54": "Other cup match",
    "55": "Overuse (repetitive mechanism)",
    "56": "Trauma (acute mechanism)",
    "57": "Gradual onset",
    "58": "Sudden onset",
    "59": "No",
    "60": "Yes, direct contact (to injured body part)",
    "61": "Yes, indirect contact (to other body part)",
    "62": "Running/sprinting",
    "63": "Heading",
    "64": "Controlling the ball",
    "65": "Tackling other player",
    "66": "Blocked*",
    "67": "Twisting/turning",
    "68": "Landing (incl. jumping)",
    "69": "Hit by ball",
    "70": "Tackled by other player",
    "71": "Use of arm/elbow*",
    "72": "Shooting/passing",
    "73": "Falling (incl. diving)",
    "74": "Collision",
    "75": "Sliding/stretching*",
    "76": "Other player action",
    "77": "No",
    "78": "Yes (give date of return from previous injury)",
    "79": "No foul",
    "80": "Opponent foul",
    "81": "Own foul",
    "82": "Yellow card",
    "83": "Red card",
    "84": "Clinical only",
    "85": "X-ray",
    "86": "Ultrasonography",
    "87": "MRI",
    "88": "Other (specify)",
    "89": "No",
    "90": "Yes",
    "91": "No",
    "92": "Yes",
    "93": "No",
    "94": "Yes (specify)",
    "95": "No",
    "96": "Yes (specify)",
}


checkbox_map_by_type = {
    "HEAD": {
    # Location of impact on head and/or body
    "1": "Left",
    "2": "Face (eyes & below)",
    "3": "Temporal",
    "4": "Cervical",
    "5": "Right",
    "5": "Frontal",
    "7": "Parietal",
    "8": "Ear(s)",
    "9": "Midline",
    "10": "Middle / Central",
    "11": "Occipital",
    "12": "Other",
    
    # Injury type
    "13": "Contusion",
    "14": "Fracture",
    "15": "Laceration",
    "16": "Concussion",
    "17": "Dental",
    "18": "Mild Traumatic Brain Injury (TBI) with abnormality on MRI:",
    "19": "Moderate TBI",
    "20": "Severe TBI",
    "21": "Other",

    # When did the injury occur? - Onset during
    "22": "Training",
    "23": "Match",
    "24": "N/A (Gradual onset injury)",
    
    # When did the injury occur? - Type of training/match
    "25": "Football training",
    "26": "Football & other training",
    "27": "Champions League",
    "28": "Other cup match",
    "29": "Other training",
    "30": "Reserve/youth team training",
    "31": "Europa League",
    "32": "Friendly match",
    "33": "National team",
    "34": "League match",
    "35": "Europa Conference League",
    "36": "Reserve/youth team match",
    
    # Injury mechanisms and player actions
    "37": "Overuse (Repetitive mechanism)",
    "38": "Trauma (Acute mechanism)",
    "39": "Gradual onset",
    "40": "Sudden onset",
    "41": "Yes",
    "42": "No",
    "43": "No",
    "44": "Yes, with opponent",
    "45": "Yes, with teammate",
    "46": "Yes, with object",
    
    # In case of player contact, head contact was made with:
    "47": "Head",
    "48": "Shoulder",
    "49": "Elbow",
    "50": "Knee",
    "51": "Other body part",
    
    # In case of object contact, head contact was made with:
    "52": "Goalpost",
    "53": "Pitch / Surface",
    "54": "Ball, intended header",
    "55": "Ball, unintended",
    "56": "Other object",
    
    # Circumstances and player's actions at time of injury
    "57": "Running/sprinting",
    "58": "Heading",
    "59": "Controlling the ball",
    "60": "Tackling other player",
    "61": "Blocked",
    "62": "Twisting/turning",
    "63": "Landing (incl. jumping)",
    "64": "Hit by ball",
    "65": "Tackled by other player",
    "66": "Use of arm/elbow",
    "67": "Shooting/passing",
    "68": "Falling (incl. diving)",
    "69": "Collision",
    "70": "Sliding/stretching",
    "71": "Other player action",
    
    # Other information - Was this a re-injury?
    "72": "No",
    "73": "Unknown",
    "74": "Yes",
    
    # Referee's sanction
    "75": "No foul",
    "76": "Yellow card",
    "77": "Opponent foul",
    "78": "Red card",
    "79": "Own foul",
    
    # Was the player substituted?
    "80": "Yes, immediately",
    "81": "Yes",
    "82": "No",
    
    # Did you use the medical review system?
    "83": "Yes",
    "84": "No",
    "85": "Not accessible",
    
    # In case of concussion - Affected clinical domains
    "86": "Cognition (e.g. confusion, difficulties remembering...)",
    "87": "Headache/Migraine (e.g. head/neck pain, sensitivity to light / noise...)",
    "88": "General fatigue (e.g. low energy...)",
    "89": "Anxiety/Mood (e.g. sadness, irritability, emotional...)",
    "90": "Vestibular (e.g. balance problems, dizziness...)",
    "91": "Ocular (e.g. blurry or double vision etc...)",
    "92": "Other",
    },
    "INJURY": {
    # Injury location
    "1": "Neck",
    "2": "Shoulder",
    "3": "Hand",
    "4": "Lower leg (incl. Achilles tendon)",
    "5": "Chest",
    "6": "Upper arm",
    "7": "Hip",
    "8": "Ankle",
    "9": "Thoracic spine",
    "10": "Elbow",
    "11": "Groin",
    "12": "Foot",
    "13": "Abdomen",
    "14": "Forearm",
    "15": "Thigh",
    "16": "Other",
    "17": "Lumbosacral",
    "18": "Wrist",
    "19": "Knee",
    
    # Injury side
    "20": "Right",
    "21": "Left",
    "22": "Bilateral/central",
    
    # Injury type
    "23": "Abrasion",
    "24": "Joint dislocation/subluxation",
    "25": "Other bone injury (e.g., bone stress injury)",
    "26": "Arthritis/synovitis/capsulitis",
    "27": "Joint sprain (i.e., ligament/capsule)",
    "28": "Overuse unspecified",
    "29": "Bursitis",
    "30": "Laceration",
    "31": "Tendon rupture/tendinopathy",
    "32": "Cartilage lesion",
    "33": "Muscle rupture/tear/strain",
    "34": "Vessel injury (excl. skin haematoma)",
    "35": "Fracture (Specify if stress fracture)",
    "36": "Haematoma/contusion/bruise (incl. compartment syndrome)",
    "37": "Nerve injury (central or peripheral other than concussion)",
    "38": "Other",
    
    # When did the injury occur? - Onset during
    "39": "Training",
    "40": "Match",
    "41": "N/A (Gradual onset injury)",
    
    # When did the injury occur? - Type of training/match
    "42": "Football training",
    "43": "Football & other training",
    "44": "Champions League",
    "45": "Other cup match",
    "46": "Other training",
    "47": "Reserve/youth team training",
    "48": "Europa League",
    "49": "Friendly match",
    "50": "National team",
    "51": "League match",
    "52": "Europa Conference League",
    "53": "Reserve/youth team match",
    
    # Injury mechanisms and player actions - Overuse or trauma?
    "54": "Overuse (Repetitive mechanism)",
    "55": "Trauma (Acute mechanism)",
    
    # Did symptoms have a gradual or sudden onset?
    "56": "Gradual onset",
    "57": "Sudden onset",
    
    # Was the injury caused by contact?
    "58": "Yes, direct contact (to injured body part)",
    "59": "Yes, indirect contact (to other body part)",
    "60": "No",
    
    # Circumstances and player's actions at time of injury
    "61": "Running/sprinting",
    "62": "Heading",
    "63": "Controlling the ball",
    "64": "Tackling other player",
    "65": "Blocked",
    "66": "Twisting/turning",
    "67": "Landing (incl. jumping)",
    "68": "Hit by ball",
    "69": "Tackled by other player",
    "70": "Use of arm/elbow",
    "71": "Shooting/passing",
    "72": "Falling (incl. diving)",
    "73": "Collision",
    "74": "Sliding/stretching",
    "75": "Other player action",
    
    # Other information - Was this a re-injury?
    "76": "No",
    "77": "Unknown",
    "78": "Yes",
    
    # Referee's sanction
    "79": "No foul",
    "80": "Yellow card",
    "81": "Opponent foul",
    "82": "Red card",
    "83": "Own foul",
    
    # Diagnostic examination
    "84": "Clinical only",
    "85": "Ultrasonography",
    "86": "Arthroscopy",
    "87": "X-ray",
    "88": "MRI",
    "89": "Other",
    
    # Was any surgery performed?
    "90": "Yes",
    "91": "No",
    "92": "Unknown",
    },
    "ILLNESS": {
    # Type of illness
    "1": "Infection in airways (incl. influenza, common cold)",
    "2": "Stomach pain, diarrhoea or bowel problems",
    "3": "Infection in other organs/body parts",
    "4": "Headache, migraine, or nausea",
    "5": "Asthma or allergies",
    "6": "Unexplained fatigue, malaise or fever",
    "7": "Other",
    
    # If other illness, please select affected organ system
    "8": "Respiratory",
    "9": "Dermatological",
    "10": "Cardiovascular",
    "11": "Neurological",
    "12": "Renal/urogenital/gynaecological",
    "13": "Psychiatric and behavioural",
    "14": "Metabolic/endocrinological",
    "15": "Ophthalmic/otorhinolaryngological",
    "16": "Haematological",
    "17": "Dental",
    "18": "Rheumatological/connective tissue disorder",
    "19": "Environmental (including heat/altitude illness)",
    "20": "Immunological",
    "21": "Other",
    
    # Other information - Was this a recurrence?
    "22": "No",
    "23": "Unknown",
    "24": "Yes",
    },
    "KNEE": {
    # Combination of injuries
    "1": "ACL",
    "2": "MCL",
    "3": "PCL",
    "4": "LCL",
    "5": "MPFL",
    "6": "Medial meniscus",
    "7": "Lateral meniscus",
    "8": "Popliteus",
    "9": "Biceps femoris",
    "10": "Cartilage MFC",
    "11": "Cartilage MTC",
    "12": "Cartilage LFC",
    "13": "Cartilage LTC",
    "14": "Cartilage PF",
    "15": "Other",
    
    # Injury side
    "16": "Right",
    "17": "Left",
    "18": "Bilateral",
    
    # Injury grading - ACL
    "19": "Partial",
    "20": "Total",
    
    # Injury grading - MCL
    "21": "Grade 1",
    "22": "Grade 2",
    "23": "Grade 3",
    
    # When did the injury occur? - Onset during
    "24": "Training",
    "25": "Match",
    "26": "N/A (Gradual onset injury)",
    
    # When did the injury occur? - Type of training/match
    "27": "Football training",
    "28": "Football & other training",
    "29": "Champions League",
    "30": "Other cup match",
    "31": "Other training",
    "32": "Reserve/youth team training",
    "33": "Europa League",
    "34": "Friendly match",
    "35": "National team",
    "36": "League match",
    "37": "Europa Conference League",
    "38": "Reserve/youth team match",
    
    # Injury mechanisms and player actions - Overuse or trauma?
    "39": "Overuse (Repetitive mechanism)",
    "40": "Trauma (Acute mechanism)",
    
    # Did symptoms have a gradual or sudden onset?
    "41": "Gradual onset",
    "42": "Sudden onset",
    
    # Was the injury caused by contact?
    "43": "Yes, direct contact (to injured body part)",
    "44": "Yes, indirect contact (to other body part)",
    "45": "No",
    
    # Circumstances and player's actions at time of injury
    "46": "Running/sprinting",
    "47": "Heading",
    "48": "Controlling the ball",
    "49": "Tackling player",
    "50": "Blocked",
    "51": "Twisting/turning",
    "52": "Landing (incl. jumping)",
    "53": "Hit by ball",
    "54": "Tackled by player",
    "55": "Use of arm/elbow",
    "56": "Shooting/passing",
    "57": "Falling (incl. diving)",
    "58": "Collision",
    "59": "Sliding/stretching",
    "60": "Other player action",
    
    # Other information - Was this a re-injury?
    "61": "No",
    "62": "Unknown",
    "63": "Yes",
    
    # Previous contralateral injury of same diagnosis?
    "64": "No",
    "65": "Unknown",
    "66": "Yes",
    
    # Referee's sanction
    "67": "No foul",
    "68": "Yellow card",
    "69": "Opponent foul",
    "70": "Red card",
    "71": "Own foul",
    
    # Diagnostic examination
    "72": "Clinical only",
    "73": "Ultrasonography",
    "74": "Arthroscopy",
    "75": "X-ray",
    "76": "MRI",
    "77": "Other",
    
    # Was any bracing used?
    "78": "Yes",
    "79": "No",
    "80": "Unknown",
    
    # Was any surgery performed?
    "81": "Yes",
    "82": "No",
    "83": "Unknown",
    
    # ACL repair/reconstruction
    "84": "No repair/reconstruction",
    "85": "Quadriceps tendon",
    "86": "LET/ALL",
    "87": "Patella tendon",
    "88": "Iliotibial band",
    "89": "Allograft",
    "90": "Hamstring tendon",
    "91": "Other",
    
    # MCL repair/reconstruction
    "92": "No repair/reconstruction",
    "93": "Synthetic",
    "94": "Allograft",
    "95": "Hamstring tendon",
    "96": "Other",
    },
    "LOWER_EXTREMITIES": {
    # Location of injury
    "1": "Adductor longus",
    "2": "Vastus lateralis",
    "3": "Biceps femoris",
    "4": "Semimembranosus",
    "5": "Adductor brevis",
    "6": "Vastus medialis",
    "7": "Rectus femoris",
    "8": "Semitendinosus",
    "9": "Adductor magnus",
    "10": "Vastus intermedius",
    "11": "Gastrocnemius",
    "12": "Soleus",
    "13": "Pectineus",
    "14": "Gracilis",
    "15": "Other",
    
    # Injury side
    "16": "Right",
    "17": "Left",
    "18": "Bilateral",
    
    # Injury site
    "19": "Proximal",
    "20": "Middle",
    "21": "Distal",
    
    # Injury type
    "22": "Muscle rupture/tear/strain",
    "23": "Intramuscular tendon rupture/tear/strain",
    "24": "Avulsion fracture to tendon attachment site",
    "25": "Hypertonia/spasm/trigger points",
    
    # Injury classification
    "26": "Fatigue-induced muscle disorder",
    "27": "Partial muscle injury - minor",
    "28": "Delayed onset muscle soreness",
    "29": "Partial muscle injury - moderate",
    "30": "Neuromuscular muscle disorder - spine related",
    "31": "Complete/subtotal muscle injury - severe",
    "32": "Neuromuscular muscle disorder - muscle related",
    
    # When did the injury occur? - Onset during
    "33": "Training",
    "34": "Match",
    "35": "N/A (Gradual onset injury)",
    
    # When did the injury occur? - Type of training/match
    "36": "Football training",
    "37": "Football & other training",
    "38": "Champions League",
    "39": "Other cup match",
    "40": "Other training",
    "41": "Reserve/youth team training",
    "42": "Europa League",
    "43": "Friendly match",
    "44": "National team",
    "45": "League match",
    "46": "Europa Conference League",
    "47": "Reserve/youth team match",
    
    # Injury mechanisms and player actions - Overuse or trauma?
    "48": "Overuse (Repetitive mechanism)",
    "49": "Trauma (Acute mechanism)",
    
    # Did symptoms have a gradual or sudden onset?
    "50": "Gradual onset",
    "51": "Sudden onset",
    
    # Was the injury caused by contact?
    "52": "Yes, direct contact (to injured body part)",
    "53": "Yes, indirect contact (to other body part)",
    "54": "No",
    
    # Circumstances and player's actions at time of injury
    "55": "Running/sprinting",
    "56": "Heading",
    "57": "Controlling the ball",
    "58": "Tackling player",
    "59": "Blocked",
    "60": "Twisting/turning",
    "61": "Landing (incl. jumping)",
    "62": "Hit by ball",
    "63": "Tackled by player",
    "64": "Use of arm/elbow",
    "65": "Shooting/passing",
    "66": "Falling (incl. diving)",
    "67": "Collision",
    "68": "Sliding/stretching",
    "69": "Other player action",
    
    # Other information - Was this a re-injury?
    "70": "No",
    "71": "Unknown",
    "72": "Yes",
    
    # Referee's sanction
    "73": "No foul",
    "74": "Yellow card",
    "75": "Opponent foul",
    "76": "Red card",
    "77": "Own foul",
    
    # Diagnostic examination
    "78": "Clinical only",
    "79": "Ultrasonography",
    "80": "Arthroscopy",
    "81": "X-ray",
    "82": "MRI",
    "83": "Other",
    
    # Was any surgery performed?
    "84": "Yes",
    "85": "No",
    "86": "Unknown",
    },
    "OTHER": {
    },
}


        