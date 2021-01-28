# Author: Mario Königbauer
# License: GNU General Public License v3.0

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsField, QgsFeature, QgsProcessing, QgsExpression, QgsGeometry, QgsPoint, QgsFields, QgsWkbTypes, QgsStringUtils,
                       QgsProcessingAlgorithm, QgsProcessingParameterField, QgsProcessingParameterVectorLayer, QgsProcessingOutputVectorLayer, QgsProcessingParameterEnum, QgsProcessingParameterString, QgsProcessingParameterNumber)

class SelectDuplicatesBySimilarity(QgsProcessingAlgorithm):
    SOURCE_LYR = 'SOURCE_LYR'
    SOURCE_FIELD = 'SOURCE_FIELD'
    MAX_DISTANCE = 'MAX_DISTANCE'
    ALGORITHM = 'ALGORITHM'
    ANDORALG = 'ANDORALG'
    THRESHOLD = 'THRESHOLD'
    OPERATOR = 'OPERATOR'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.SOURCE_LYR, self.tr('Source Layer'))) # Take any source layer
        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_FIELD, self.tr('Attribute Field to search for similarity'),'Name','SOURCE_LYR')) # Choose the Trigger field of the source layer, default if exists is 'Trigger'
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_DISTANCE, self.tr('Maximum Search Distance for Duplicates in Layer CRS units'),1,10000))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ALGORITHM, self.tr('Select the Algorithms you want to use to identify similar attributes.'),
                    ['Exact Duplicates',
                    'Soundex',
                    'Levenshtein Distance',
                    'Longest Common Substring',
                    'Hamming Distance'],
                    allowMultiple=True,defaultValue=[0,1,2]))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ANDORALG, self.tr('Choose if all selected algorithms need to fulfill criteria or only at least one'),['All','Only at least one'],defaultValue=0))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD, self.tr('Choose a Threshold for these three algorithms: \nLevenshtein < Threshold \nLongest Common Substring > Threshold \nHamming Distance > Threshold'),0,5))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT, self.tr('Possible Duplicates')))

    def processAlgorithm(self, parameters, context, feedback):
        # Get Parameters and assign to variable to work with
        layer = self.parameterAsLayer(parameters, self.SOURCE_LYR, context)
        field = self.parameterAsString(parameters, self.SOURCE_FIELD, context)
        maxdist = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)
        th = self.parameterAsInt(parameters, self.THRESHOLD, context)
        alg = self.parameterAsEnums(parameters, self.ALGORITHM, context)
        ao = self.parameterAsInt(parameters, self.ANDORALG, context)
        op = self.parameterAsString(parameters, self.OPERATOR, context)
        
        total = 100.0 / layer.featureCount() if layer.featureCount() else 0 # Initialize progress for progressbar
        
        layer.removeSelection()
        
        for current, feat in enumerate(layer.getFeatures()): # iterate over source 
            s = None # reset selection indicator
            s0 = None
            s1 = None
            s2 = None
            s3 = None
            s4 = None
            for lookup in layer.getFeatures():  # compare to every feature of same layer
                if feat.id() > lookup.id(): # only compare if not already done so
                    if feat.geometry().centroid().distance(lookup.geometry().centroid()) <= maxdist: # only select if within given maxdistance
                        if 0 in alg: # Exact Duplicates
                            if feat[field] == lookup[field]:
                                s0 = 1
                            else: s0 = 0
                        if 1 in alg: # Soundex
                            if QgsStringUtils.soundex(feat[field]) == QgsStringUtils.soundex(lookup[field]):
                                s1 = 1
                            else: s1 = 0
                        if 2 in alg: # Levenshtein
                            if QgsStringUtils.levenshteinDistance(feat[field],lookup[field]) < th:
                                s2 = 1
                            else: s2 = 0
                        if 3 in alg: # Longest Common Substring
                            if len(QgsStringUtils.longestCommonSubstring(feat[field],lookup[field])) > th:
                                s3 = 1
                            else: s3 = 0
                        if 4 in alg: # Hamming Distance:
                            if QgsStringUtils.hammingDistance(feat[field],lookup[field]) > th:
                                s4 = 1  
                            else: s4 = 0
                            
                        if ao == 0: # All chosen algorithms need to match
                            if 0 in (s0, s1, s2, s3, s4): # Dont select current feature if at least one used algorithm returned 0
                                s = 0
                            else: # Select current feature if all algorithms returned 1 or None
                                s = 1
                        elif ao == 1: # Only at least one algorithm needs to match
                            if 1 in (s0, s1, s2, s3, s4): # Select current feature if at least one used algorithm returned 1
                                s = 1
                            else: # Dont select current feature if no used algorithm returned 1
                                s = 0
                                
                        if s == 1: # select the current feature if indicator is true
                            layer.select(feat.id())
                            
                        
            
            feedback.setProgress(int(current * total)) # Set Progress in Progressbar
            if feedback.isCanceled(): # Cancel algorithm if button is pressed
                break

        return {self.OUTPUT: parameters[self.SOURCE_LYR]} # Return result of algorithm

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SelectDuplicatesBySimilarity()

    def name(self):
        return 'SelectDuplicatesBySimilarity'

    def displayName(self):
        return self.tr('Select duplicate features by similarity')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr(
        'This Algorithm selects possible duplicate features by their similarity. The first feature (ordered by feature id) in each group is NOT beeing selected. '
        'You can choose between the following algorithms, and can also combine them: \n'
        '- Exact Match: Matches if the attribue values are exactly the same \n'
        '- Soundex: Matches by sound, as pronounced in English both values are equal \n '
        '- Levenshtein Distance: Matches if by measuring the difference between two sequences is lower than the threshold\n '
        '- Longest Common Substring: Matches if the longest string that is a substring of compared value and greater than the threshold \n'
        '- Hamming Distance: Matches if between two strings of equal length the number of positions at which the corresponding symbols are greater than the threshold \n '
        'You can also choose a maximum search distance in CRS units. If the layer is not a single-point layer, the centroids are taken for distance calculation.'
        )