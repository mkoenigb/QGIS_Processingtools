# Author: Mario Königbauer based on answer by Kadir Şahbaz: https://gis.stackexchange.com/a/363630/107424
# License: GNU General Public License v3.0

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsField, QgsFeature, QgsProcessing, QgsExpression,
                       QgsFeatureSink, QgsFeatureRequest, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterField, QgsProcessingParameterFeatureSource, QgsProcessingParameterEnum)

class ClosestPointWithAttributeCondition(QgsProcessingAlgorithm):
    POSSIBILITY_LYR = 'POSSIBILITY_LYR'
    POSSIBILITY_IDFIELD = 'POSSIBILITY_IDFIELD'
    POSSIBILITY_POLYGONFIELD = 'POSSIBILITY_POLYGONFIELD'
    STOP_LYR = 'STOP_LYR'
    STOP_IDFIELD = 'STOP_IDFIELD'
    STOP_POLYGONFIELD = 'STOP_POLYGONFIELD'
    OPERATION = 'OPERATION'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STOP_LYR, self.tr('Source (Find nearest Points for this Layer)'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(
            QgsProcessingParameterField(
                self.STOP_IDFIELD, self.tr('Unique ID Field of Source Layer (Any Datatype)'),'ANY','STOP_LYR'))        
        self.addParameter(
            QgsProcessingParameterField(
                self.STOP_POLYGONFIELD, self.tr('Matching ID Field of Source Layer (Numerical)'),'ANY','STOP_LYR',0))  
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POSSIBILITY_LYR, self.tr('Possibilities (Find Points on this Layer)'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(
            QgsProcessingParameterField(
                self.POSSIBILITY_IDFIELD, self.tr('Unique Possibility ID Field (Any Datatype, should have a different name than Source ID field)'),'ANY','POSSIBILITY_LYR'))
        self.addParameter(
            QgsProcessingParameterField(
                self.POSSIBILITY_POLYGONFIELD, self.tr('Matching ID Field of Possibilities Layer (Numerical)'),'ANY','POSSIBILITY_LYR',0))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OPERATION, self.tr('Matching ID Operation (Currently only != and = do work)'), ['!=','=','<','>','<=','>='])) #Only != and = will work here due to expression below
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, self.tr('Output Layer'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        # Get Parameters
        possibility_layer = self.parameterAsSource(parameters, self.POSSIBILITY_LYR, context)
        possibility_idfield = self.parameterAsFields(parameters, self.POSSIBILITY_IDFIELD, context)
        possibility_polygonfield = self.parameterAsFields(parameters, self.POSSIBILITY_POLYGONFIELD, context)
        stop_layer = self.parameterAsSource(parameters, self.STOP_LYR, context)
        stop_polygonfield = self.parameterAsFields(parameters, self.STOP_POLYGONFIELD, context)
        stop_idfield = self.parameterAsFields(parameters, self.STOP_IDFIELD, context)
        operation = self.parameterAsString(parameters, self.OPERATION, context)
        operationlist = [' != ',' = ',' < ',' > ',' <= ',' >= ']
        expressionoperator = str(operationlist[int(operation[0])])        

        fields = possibility_layer.fields()
        fields.append(QgsField(stop_idfield[0]))
        fields.append(QgsField("join_dist", QVariant.Double, len=20, prec=5))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, possibility_layer.wkbType(),
                                               possibility_layer.sourceCrs())

        # iterate over stop features
        for stop_feat in stop_layer.getFeatures():
            # request string for points which have different polygonid
            request = QgsFeatureRequest(QgsExpression(possibility_polygonfield[0] + expressionoperator + str(stop_feat[stop_polygonfield[0]])))
            distances = {p: stop_feat.geometry().distance(p.geometry())
                             for p in possibility_layer.getFeatures(request)}

            # get the feature which has the minimum distance value
            nearest_point = min(distances, key=distances.get)

            # create a new feature, set geometry and populate the fields
            new_feat = QgsFeature(fields)
            new_feat.setGeometry(nearest_point.geometry())
            new_feat[possibility_idfield[0]] = nearest_point[possibility_idfield[0]]
            new_feat[possibility_polygonfield[0]] = nearest_point[possibility_polygonfield[0]]
            new_feat[stop_idfield[0]] = stop_feat[stop_idfield[0]]
            new_feat["join_dist"] = distances[nearest_point]

            # add nearest_point feature to the new layer
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ClosestPointWithAttributeCondition()

    def name(self):
        return 'ClosestPointWithAttributeCondition'

    def displayName(self):
        return self.tr('Closest Point With Attribute Condition')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr('This Algorithm finds the Sourcelayer`s closest Possibility-Points according the Operation on the Matching ID. The result is an extraction of the Possibilitylayer having the Possibility ID, Matching ID, Source ID and Join Distance.')