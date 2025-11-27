"""
Script de prueba para validar las funciones de parseo y cálculo de encuesta_app.py
"""

import sys
sys.path.insert(0, '.')

from encuesta_app import try_int, parse_adults_minors, compute_meat_suggestion

def test_try_int():
    print("🧪 Testing try_int()...")
    assert try_int("5") == 5
    assert try_int("10 personas") == 10
    assert try_int("abc") == "abc"
    assert try_int(None) is None
    assert try_int(7) == 7
    print("✅ try_int() passed all tests")

def test_parse_adults_minors():
    print("\n🧪 Testing parse_adults_minors()...")
    
    # Test cases
    test_cases = [
        ("2 adultos, 1 menor", (2, 1)),
        ("3 adultos 2 niños", (3, 2)),
        ("adultos: 2 menores: 1", (2, 1)),
        ("5", (5, 0)),  # solo un número, asume adultos
        ("2 menores", (0, 2)),
        ("todos adultos", (None, None)),
        ("", (None, None)),
    ]
    
    for text, expected in test_cases:
        result = parse_adults_minors(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected {expected})")

def test_compute_meat_suggestion():
    print("\n🧪 Testing compute_meat_suggestion()...")
    
    # Caso 1: Respuestas con adultos/menores explícitos
    responses1 = [
        {
            "¿Cuántas personas vienen contigo?": "3",
            "Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)": "2 adultos, 1 menor"
        },
        {
            "¿Cuántas personas vienen contigo?": "2",
            "Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)": "2 adultos"
        }
    ]
    
    result1 = compute_meat_suggestion(responses1)
    print(f"📊 Test 1 - Explícito:")
    print(f"   Total personas: {result1['total_people_estimated']}")
    print(f"   Adultos: {result1['total_adults']}, Menores: {result1['total_minors']}")
    print(f"   Kg sugeridos: {result1['suggested_kg_total']} kg")
    
    # Expected: 4 adultos, 1 menor = 4*0.5 + 1*0.18 = 2.18 kg
    assert result1['total_adults'] == 4
    assert result1['total_minors'] == 1
    print("✅ Test 1 passed")
    
    # Caso 2: Respuestas sin desglose (solo total)
    responses2 = [
        {
            "¿Cuántas personas vienen contigo?": "5",
            "Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)": ""
        }
    ]
    
    result2 = compute_meat_suggestion(responses2)
    print(f"\n📊 Test 2 - Sin desglose:")
    print(f"   Total personas: {result2['total_people_estimated']}")
    print(f"   Adultos asumidos: {result2['total_adults']}")
    print(f"   Kg sugeridos: {result2['suggested_kg_total']} kg")
    
    # Expected: 5 personas asumidas como adultos = 5*0.5 = 2.5 kg
    assert result2['total_adults'] == 5
    assert result2['total_minors'] == 0
    print("✅ Test 2 passed")
    
    # Caso 3: Vacío
    responses3 = []
    result3 = compute_meat_suggestion(responses3)
    print(f"\n📊 Test 3 - Sin respuestas:")
    print(f"   Kg sugeridos: {result3['suggested_kg_total']} kg")
    assert result3['suggested_kg_total'] == 0
    print("✅ Test 3 passed")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBAS DE VALIDACIÓN - encuesta_app.py")
    print("=" * 60)
    
    try:
        test_try_int()
        test_parse_adults_minors()
        test_compute_meat_suggestion()
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
