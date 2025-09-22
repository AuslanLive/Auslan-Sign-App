# Import torch for model
import pandas as pd
from tensorflow.keras.models import *
import json
import numpy as np
import tensorflow as tf
import asyncio
import os

# Define a custom layer so that the model can load
CLASS_LABEL_PATH = os.path.join('app', r"class_label_index.json")

@tf.keras.utils.register_keras_serializable()
class ExpandAxisLayer(tf.keras.layers.Layer):
    def __init__(self, axis=1, **kwargs):
        super(ExpandAxisLayer, self).__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        return tf.expand_dims(inputs, axis=self.axis)

    def get_config(self):
        config = super(ExpandAxisLayer, self).get_config()
        config.update({"axis": self.axis})
        return config


class Model:
    def __init__(self, model_path):
        # Setting base variables
        self.model_path = model_path

        # Just remember that indexed are strings
        # Opening the classes
        with open(CLASS_LABEL_PATH) as f:
            self.outputs = json.load(f)

        # Create model here
        self.model = load_model(filepath=model_path)

    async def query_model(self, keypoints):
        # print("IN QUERY")
        # Format keypoints so it fits the model
        formatted_keypoints = self.__format_input_keypoints(keypoints)

        # Query the model
        result = await self.__get_model_result(formatted_keypoints)

        # Parse results so it fits the formate needed
        final_result = self.__format_model_results(result)
        # print("FORMATTE RESSULTS")
        return final_result

    ############################# Private helper functions needed for query model #############################
    def __format_input_keypoints(self, keypoints):
        #! PLEASE GIVE SHAPE WITH (number_of_frames, number_of_keypoints, 1, features)

        # probs just padd the dataframe so it fits the inputs
        keypoints = np.expand_dims(keypoints, axis=0)  # Add a batch dimension

        return keypoints

    async def __get_model_result(self, keypoints):
        # print("CALLINGTHE MODEEL")
        # just query the model
        result = await asyncio.to_thread(self.model.predict, keypoints, verbose=2)
        return result[0]

    def __format_model_results(self, result):
        # Loop through resuklts and append the correct class to the probability

        fomated_results = {"model_output": []}
        for i in range(len(result)):
            # Adding the results
            str_index = str(i)
            fomated_results['model_output'].append(
                [self.outputs[str_index], result[i]])

        fomated_results['model_output'] = sorted(
            fomated_results['model_output'], key=lambda x: float(x[1]), reverse=True)[:10]

        return fomated_results
    ############################# Private helper functions needed for query model #############################
