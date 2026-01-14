from google.cloud import firestore

def test_firestore_connection():
    try:
        # Initialize Firestore client
        db = firestore.Client()
        print("Connected to Firestore!")

        # Test Firestore write
        doc_ref = db.collection("test").document("sample_document")
        doc_ref.set({"key": "value"})
        print("Firestore document written successfully!")
    except Exception as e:
        print(f"Error: {e}")

test_firestore_connection()