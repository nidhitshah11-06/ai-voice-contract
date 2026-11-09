LANGS = {
    "hi-IN": "Hindi", "en-IN": "English", "mr-IN": "Marathi", "gu-IN": "Gujarati",
    "bn-IN": "Bengali", "kn-IN": "Kannada", "ml-IN": "Malayalam",
    "pa-IN": "Punjabi", "ta-IN": "Tamil", "te-IN": "Telugu",
}

# weekday index (Mon=0) -> keywords, all lowercase. Best-effort: only Hindi is tested
# against real Prisma output, so confirm other languages with one real clip each.
DAYS = {
    0: ["monday", "somvar", "सोमवार", "સોમવાર", "সোমবার", "ਸੋਮਵਾਰ", "ಸೋಮವಾರ", "సోమవారం", "திங்கள்", "തിങ്കൾ"],
    1: ["tuesday", "mangalvar", "मंगलवार", "मंगळवार", "મંગળવાર", "মঙ্গলবার", "ਮੰਗਲਵਾਰ", "ಮಂಗಳವಾರ", "మంగళవారం", "செவ்வாய்", "ചൊവ്വ"],
    2: ["wednesday", "budhvar", "बुधवार", "બુધવાર", "বুধবার", "ਬੁੱਧਵਾਰ", "ಬುಧವಾರ", "బుధవారం", "புதன்", "ബുധൻ"],
    3: ["thursday", "guruvar", "brihaspativar", "गुरुवार", "बृहस्पतिवार", "ગુરુવાર", "বৃহস্পতিবার", "ਵੀਰਵਾਰ", "ಗುರುವಾರ", "గురువారం", "வியாழன்", "വ്യാഴം"],
    4: ["friday", "shukravar", "शुक्रवार", "શુક્રવાર", "শুক্রবার", "ਸ਼ੁੱਕਰਵਾਰ", "ಶುಕ್ರವಾರ", "శుక్రవారం", "வெள்ளி", "വെള്ളി"],
    5: ["saturday", "shanivar", "शनिवार", "શનિવાર", "শনিবার", "ਸ਼ਨੀਵਾਰ", "ಶನಿವಾರ", "శనివారం", "சனி", "ശനി"],
    6: ["sunday", "ravivar", "itvar", "रविवार", "इतवार", "રવિવાર", "রবিবার", "ਐਤਵਾਰ", "ಭಾನುವಾರ", "ఆదివారం", "ஞாயிறு", "ഞായർ"],
}