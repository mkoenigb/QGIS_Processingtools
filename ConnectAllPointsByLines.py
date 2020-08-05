from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsField, QgsFeature, QgsProcessing, QgsExpression, QgsGeometry, QgsPoint, QgsFields, QgsWkbTypes,
                       QgsFeatureSink, QgsFeatureRequest, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterField, QgsProcessingParameterFeatureSource, QgsProcessingParameterEnum)

class ConnectAllPointsByLines(QgsProcessingAlgorithm):
    POSSIBILITY_LYR = 'POSSIBILITY_LYR'
    POSSIBILITY_IDFIELD = 'POSSIBILITY_IDFIELD'
    STOP_LYR = 'STOP_LYR'
    STOP_IDFIELD = 'STOP_IDFIELD'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STOP_LYR, self.tr('Source Points'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(
            QgsProcessingParameterField(
                self.STOP_IDFIELD, self.tr('Unique ID Field of Source Layer (Any Datatype)'),'ANY','STOP_LYR'))        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POSSIBILITY_LYR, self.tr('Target Points'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(
            QgsProcessingParameterField(
                self.POSSIBILITY_IDFIELD, self.tr('Unique Target ID Field (Any Datatype, should have a different name than Source ID field)'),'ANY','POSSIBILITY_LYR'))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, self.tr('Line Connections'), QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        # Get Parameters
        possibility_layer = self.parameterAsSource(parameters, self.POSSIBILITY_LYR, context)
        possibility_idfield = self.parameterAsFields(parameters, self.POSSIBILITY_IDFIELD, context)
        stop_layer = self.parameterAsSource(parameters, self.STOP_LYR, context)
        stop_idfield = self.parameterAsFields(parameters, self.STOP_IDFIELD, context)

        fields = QgsFields()
        fields.append(QgsField(stop_idfield[0]))        
        fields.append(QgsField(possibility_idfield[0]))
        fields.append(QgsField("line_length", QVariant.Double, len=20, prec=5))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.LineString,
                                               possibility_layer.sourceCrs())

        # iterate over stop features
        for stop_feat in stop_layer.getFeatures():
            point1 = QgsPoint(stop_feat.geometry().asPoint())
            for source_feat in possibility_layer.getFeatures():
                point2 = QgsPoint(source_feat.geometry().asPoint())
                new_feat = QgsFeature(fields)
                new_feat.setGeometry(QgsGeometry.fromPolyline([point1, point2])) 
                new_feat[stop_idfield[0]] = stop_feat[stop_idfield[0]]                
                new_feat[possibility_idfield[0]] = source_feat[possibility_idfield[0]]
                new_feat["line_length"] = new_feat.geometry().length()                
                sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
            
        return {self.OUTPUT: dest_id}


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ConnectAllPointsByLines()

    def name(self):
        return 'ConnectAllPointsByLines'

    def displayName(self):
        return self.tr('Connect All Points By Lines')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr('This Algorithm connects all points of the Source layer with all points of the Target layer with lines and adds the lines length')