import joblib

MODEL_FILE_NAME = "model.joblib"

class DigitPredictor():
    def __init__(self, modelFileName=MODEL_FILE_NAME):
        self.mModel = joblib.load(modelFileName)
    
    def predictDigit(self, digit):
        return self.mModel.predict([digit]) 