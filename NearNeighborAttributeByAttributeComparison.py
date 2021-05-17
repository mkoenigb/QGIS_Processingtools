# Author: Mario Königbauer
# License: GNU General Public License v3.0

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsSpatialIndex, QgsProcessingParameterFeatureSink, QgsFeatureSink, QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPoint, QgsWkbTypes, 
                       QgsProcessingAlgorithm, QgsProcessingParameterField, QgsProcessingParameterVectorLayer, QgsProcessingOutputVectorLayer, QgsProcessingParameterEnum, QgsProcessingParameterNumber)
import operator

class NearNeighborAttributeByAttributeComparison(QgsProcessingAlgorithm):
    SOURCE_LYR = 'SOURCE_LYR'
    SOURCE_FIELD = 'ID_FIELD'
    ATTRIBUTE_FIELD = 'ATTRIBUTE_FIELD'
    MAX_NEIGHBORS = 'MAX_NEIGHBORS'
    MAX_DISTANCE = 'MAX_DISTANCE'
    OPERATOR = 'OPERATOR'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.SOURCE_LYR, self.tr('Source Layer'))) # Take any source layer
        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_FIELD, self.tr('Attribute field containing unique IDs'),'id','SOURCE_LYR')) # Choose the Trigger field of the source layer, default if exists is 'Trigger'
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTRIBUTE_FIELD, self.tr('Attribute field for comparison'),'year','SOURCE_LYR')) # Choose the Trigger field of the source layer, default if exists is 'Trigger'        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_NEIGHBORS, self.tr('Maximum number of nearest neighbors to compare (use -1 to compare all features of the layer)'),defaultValue=1000,minValue=-1,maxValue=10000000))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_DISTANCE, self.tr('Maximum distance of nearest neighbors to compare'),defaultValue=10000,minValue=0,maxValue=10000000))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OPERATOR, self.tr('Operator to compare the attribute value (If attribute is of type string, only == and != do work)'),
                    ['<','<=','==','!=','>=','>'],defaultValue=[2]))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, self.tr('Near Neighbor Attributes'))) # Output

    def processAlgorithm(self, parameters, context, feedback):
        # Get Parameters and assign to variable to work with
        layer = self.parameterAsLayer(parameters, self.SOURCE_LYR, context)
        idfield = self.parameterAsString(parameters, self.SOURCE_FIELD, context)
        idfield_index = layer.fields().indexFromName(idfield) # get the fieldindex of the id field
        idfield_type = layer.fields()[idfield_index].type() # get the fieldtype of this field
        attrfield = self.parameterAsString(parameters, self.ATTRIBUTE_FIELD, context)
        attrfield_index = layer.fields().indexFromName(attrfield) # get the fieldindex of the attribute field
        attrfield_type = layer.fields()[attrfield_index].type() # get the fieldtype of this field
        maxneighbors = self.parameterAsDouble(parameters, self.MAX_NEIGHBORS, context)
        maxdistance = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)
        op = self.parameterAsString(parameters, self.OPERATOR, context)
        op = int(op[0]) # get the index of the chosen operator
        #import operator
        ops = { # get the operator by the index
            0: operator.lt,
            1: operator.le,
            2: operator.eq,
            3: operator.ne,
            4: operator.ge,
            5: operator.gt
            }
        op_func = ops[op] # create the operator function
        
        total = 100.0 / layer.featureCount() if layer.featureCount() else 0 # Initialize progress for progressbar
        
        # if -1 has been chosen for maximum features to compare, use the amount of features of the layer, else use the given input
        if maxneighbors == -1:
            maxneighbors = layer.featureCount()
        
        fields = layer.fields() # get all fields of the inputlayer
        fields.append(QgsField("near_id", idfield_type)) # create new field with same type as the inputfield
        fields.append(QgsField("near_attr", attrfield_type)) # same here for the attribute field
        fields.append(QgsField("near_dist", QVariant.Double, len=20, prec=5)) # add a new field of type double
        
        idx = QgsSpatialIndex(layer.getFeatures()) # create a spatial index

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, layer.wkbType(),
                                               layer.sourceCrs())
                                               
        for current, feat in enumerate(layer.getFeatures()): # iterate over source 
            new_feat = QgsFeature(fields) # copy source fields + appended
            attridx = 0 # reset attribute fieldindex
            for attr in feat.attributes(): # iterate over attributes of source layer for the current feature
                new_feat[attridx] = attr # copy attribute values over to the new layer
                attridx += 1 # go to the next field
            new_feat.setGeometry(feat.geometry()) # copy over the geometry of the source feature
            nearestneighbors = idx.nearestNeighbor(feat.geometry(), neighbors=maxneighbors, maxDistance=maxdistance) # get the featureids of the maximum specified number of nearest neighbors within a maximum distance
            try:
                nearestneighbors.remove(feat.id()) # remove the current feature from this list (otherwise the nearest feature by == operator would always be itself...)
            except:
                pass # ignore on error
            for near in nearestneighbors: # for each feature iterate over the nearest ones
                if op_func(layer.getFeature(near)[attrfield], feat[attrfield]): # if the current nearest attribute is ? than the current feature ones, then
                    new_feat['near_id'] = layer.getFeature(near)[idfield] # get the near featureid and fill the current feature with its value
                    new_feat['near_attr'] = layer.getFeature(near)[attrfield] # also get the attribute value of this near feature
                    new_feat['near_dist'] = feat.geometry().distance(layer.getFeature(near).geometry()) # and finally calculate the distance between the current feature and the nearest matching feature
                    break # break the for loop of near features and continue with the next feat
                    
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert) # add feature to the output
            feedback.setProgress(int(current * total)) # Set Progress in Progressbar
            
            if feedback.isCanceled(): # Cancel algorithm if button is pressed
                break

        return {self.OUTPUT: dest_id} # Return result of algorithm


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return NearNeighborAttributeByAttributeComparison()

    def name(self):
        return 'NearNeighborAttributeByAttributeComparison'

    def displayName(self):
        return self.tr('Add near neighbor attribute by comparing attribute values')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr(
        'This Algorithm searches the \n'
        '- x nearest neighbors \n'
        '- within a given maximum distance \n'
        'of the current feature and compares a given attribute. \n'
        'If this comparison returns true, it adds the id, and the attribute of this neighbor to the current feature as well as the distance to this neighbor'
        )