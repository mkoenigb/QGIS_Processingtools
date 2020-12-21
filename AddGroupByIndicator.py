# Author: Mario Königbauer
# License: GNU General Public License v3.0

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsField, QgsFeature, QgsProcessing, QgsExpression, QgsGeometry, QgsPoint, QgsFields, QgsWkbTypes,
                       QgsFeatureSink, QgsFeatureRequest, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterField, QgsProcessingParameterFeatureSource, QgsProcessingParameterEnum, QgsProcessingParameterString, QgsProcessingParameterNumber)

class AddGroupByIndicator(QgsProcessingAlgorithm):
    SOURCE_LYR = 'SOURCE_LYR'
    TRIGGER_FIELD = 'TRIGGER_FIELD'
    GROUP_IDFIELD = 'GROUP_IDFIELD'
    INDICATOR_VALUE = 'INDICATOR_VALUE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SOURCE_LYR, self.tr('Source'))) # Take any source layer
        self.addParameter(
            QgsProcessingParameterField(
                self.TRIGGER_FIELD, self.tr('Trigger Field indicating a new Group'),'Trigger','SOURCE_LYR')) # Choose the Trigger field of the source layer, default if exists is 'Trigger'
        self.addParameter(
            QgsProcessingParameterString(
                self.GROUP_IDFIELD, self.tr('Name of new generated GroupID Field'),'groupid')) # String of the new added fieldname, default is 'groupid'
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INDICATOR_VALUE, self.tr('Number indicating a new Group'),0,1)) # Indicator as number. 0=Int, 1 would be double; 1=default number
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, self.tr('SourceWithGroupID'))) # Output

    def processAlgorithm(self, parameters, context, feedback):
        # Get Parameters and assign to variable to work with
        source_layer = self.parameterAsLayer(parameters, self.SOURCE_LYR, context)
        triggerfield = self.parameterAsString(parameters, self.TRIGGER_FIELD, context)
        groupfieldname = self.parameterAsString(parameters, self.GROUP_IDFIELD, context)
        newlineindicator = self.parameterAsInt(parameters, self.INDICATOR_VALUE, context)
        
        groupid = 0 # initialize groupid counter
        
        total = 100.0 / source_layer.featureCount() if source_layer.featureCount() else 0 # Initialize progress for progressbar
        
        fields = source_layer.fields() # get all fields of the sourcelayer
        fields.append(QgsField(groupfieldname, QVariant.Int, len=20)) # add a new field to this list
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, source_layer.wkbType(),
                                               source_layer.sourceCrs())
                                               
        for current, feat in enumerate(source_layer.getFeatures()): # iterate over source 
            if feat[triggerfield] == newlineindicator: # if trigger appears increase groupcounter
                groupid += 1
            new_feat = QgsFeature(fields) # copy source fields + appended
            idx = 0 # reset attribute fieldindex
            for attr in feat.attributes(): # iterate over attributes of source layer for the current feature
                new_feat[idx] = attr # copy attribute values over to the new layer
                idx += 1 # increase fieldindex counter
            new_feat[groupfieldname] = groupid # assign the groupid
            new_feat.setGeometry(feat.geometry()) # copy over the geometry of the source feature
            
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert) # add feature to the output
            
            if feedback.isCanceled(): # Cancel algorithm if button is pressed
                break
            
            feedback.setProgress(int(current * total)) # Set Progress in Progressbar

        return {self.OUTPUT: dest_id} # Return result of algorithm



    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AddGroupByIndicator()

    def name(self):
        return 'AddGroupByIndicator'

    def displayName(self):
        return self.tr('Add group by indicator field')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr('This Algorithm adds a new group id found by a trigger')