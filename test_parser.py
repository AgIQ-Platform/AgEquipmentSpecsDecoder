from parser import decode_serial

def test_decoder():
    tests = [
        {
            "serial": "1LV4052RLFH210246",
            "expected_make": "John Deere",
            "expected_model": "4052R",
            "expected_year": 2015
        },
        {
            "serial": "Z7BD03602",
            "expected_make": "New Holland",
            "expected_year": 2007
        },
        {
            "serial": "35ARLR0010882",
            "expected_make": "Case IH",
            "expected_model": "FARMALL35AII",
            "expected_year": 2025
        },
        {
            "serial": "CAT00D6KCEL700187",
            "expected_make": "Caterpillar",
            "expected_model": "D6K2LGP",
            "expected_year": 2016
        },
        {
            "serial": "1L06130MLRK500811",
            "expected_make": "John Deere",
            "expected_model": "6130M",
            "expected_year": 2025
        },
        {
            "serial": "AGCM38300GHM09283",
            "expected_make": "AGCO",
            "expected_model": "M3830",
            "expected_year": 2016
        },
        {
            "serial": "N01001",
            "expected_make": "Massey Ferguson",
            "expected_model": "399",
            "expected_year": 1988
        },
        {
            "serial": "BL01001",
            "expected_make": "Massey Ferguson",
            "expected_model": "481",
            "expected_year": 2002
        },
        {
            "serial": "JN1001",
            "expected_make": "Massey Ferguson",
            "expected_year": 2004
        },
        {
            "serial": "4352200F05077",
            "expected_make": "Fendt",
            "expected_model": "512",
            "expected_year": 2018
        },
        {
            "serial": "GE01001",
            "expected_make": "Massey Ferguson",
            "expected_model": "1235",
            "expected_year": 1998
        },
        {
            "serial": "PRK06001",
            "expected_make": "Case IH",
            "expected_model": "MAGNUM400AFSROW",
            "expected_year": 2024
        },
        {
            "serial": "JEEZC580JPF508234",
            "expected_make": "Case IH",
            "expected_model": "STEIGER 580",
            "expected_year": 2023
        },
        {
            "serial": "HEKY310FLJF001758",
            "expected_make": "New Holland",
            "expected_model": "Y310F",
            "expected_year": 2019
        },
        {
            "serial": "76007287",
            "expected_make": "Claas",
            "expected_model": "ROLLANT520RC",
            "expected_year": 2023
        },
        {
            "serial": "302338006",
            "expected_make": "Kubota",
            "expected_model": "L6060",
            "expected_year": 2013
        },
        {
            "serial": "1RW9440DASA090295",
            "expected_make": "John Deere",
            "expected_model": "9R 440",
            "expected_year": 2025
        },
        {
            "serial": "1H0X910XPSB835560",
            "expected_make": "John Deere",
            "expected_model": "X9 1000",
            "expected_year": 2025
        }
    ]

    print("\n=========================================")
    print("RUNNING PARSER VERIFICATION TESTS")
    print("=========================================\n")

    passed = 0
    for i, t in enumerate(tests):
        serial = t["serial"]
        print(f"Test {i+1}: Decoding '{serial}'...")
        res = decode_serial(serial)
        
        # Verify Make
        make_ok = res["make"] == t["expected_make"]
        print(f"  - Make: {res['make']} (Expected: {t['expected_make']}) -> {'PASSED' if make_ok else 'FAILED'}")
        
        # Verify Model if specified
        model_ok = True
        if "expected_model" in t:
            model_ok = res["model"] == t["expected_model"]
            print(f"  - Model: {res['model']} (Expected: {t['expected_model']}) -> {'PASSED' if model_ok else 'FAILED'}")
            
        # Verify Year if specified
        year_ok = True
        if "expected_year" in t:
            year_ok = res["year"] == t["expected_year"]
            print(f"  - Year: {res['year']} (Expected: {t['expected_year']}) -> {'PASSED' if year_ok else 'FAILED'}")
            
        if make_ok and model_ok and year_ok:
            print(f"  => TEST {i+1} PASSED!\n")
            passed += 1
        else:
            print(f"  => TEST {i+1} FAILED!\n")
            
    print(f"Parser Verification Results: {passed}/{len(tests)} tests passed.")
    assert passed == len(tests), "Some decoder tests failed!"

if __name__ == "__main__":
    test_decoder()
