# Author: Mario Königbauer
# License: GNU General Public License v3.0

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsField, QgsFeature, QgsProcessing, QgsExpression, QgsGeometry, QgsPoint, QgsFields, QgsWkbTypes,
                       QgsFeatureSink, QgsFeatureRequest, QgsProcessingAlgorithm, QgsSpatialIndex,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterDateTime, QgsProcessingParameterField, QgsProcessingParameterFeatureSource, QgsProcessingParameterEnum, QgsProcessingParameterString, QgsProcessingParameterNumber)
import processing
from datetime import *
import math

class CountPointsInPolygonByTime(QgsProcessingAlgorithm):
    POLYGON_LYR = 'POLYGON_LYR'
    POINT_LYR = 'POINT_LYR'
    DATETIME_FIELD = 'DATETIME_FIELD'
    START_DATETIME = 'START_DATETIME'
    END_DATETIME = 'END_DATETIME'
    INTERVALSEC = 'INTERVALSEC'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POLYGON_LYR, self.tr('Polygon'), [QgsProcessing.TypeVectorPolygon], 'polygons'))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POINT_LYR, self.tr('Point'), [QgsProcessing.TypeVectorPoint], 'points'))
        self.addParameter(
            QgsProcessingParameterField(
                self.DATETIME_FIELD, self.tr('Datetime Field'),'datetime','POINT_LYR'))
        self.addParameter(
            QgsProcessingParameterString(
                self.START_DATETIME, self.tr('Start Datetime in YYYY-MM-DD HH:MM:SS format'),'2020-01-01 00:00:00'))
        self.addParameter(
            QgsProcessingParameterString(
                self.END_DATETIME, self.tr('End Datetime in YYYY-MM-DD HH:MM:SS format'),'2020-01-10 23:59:59'))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INTERVALSEC, self.tr('Interval in Seconds'),0,86400)) # Indicator as number. 0=Int, 1 would be double; 1=default number
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, self.tr('TimePolygons with Pointcount'))) # Output

    def processAlgorithm(self, parameters, context, feedback):
        lyr_polygons = self.parameterAsLayer(parameters, self.POLYGON_LYR, context)
        lyr_points = self.parameterAsLayer(parameters, self.POINT_LYR, context)
        fld_time = self.parameterAsString(parameters, self.DATETIME_FIELD, context)
        start_date_string = self.parameterAsString(parameters, self.START_DATETIME, context)
        end_date_string = self.parameterAsString(parameters, self.END_DATETIME, context)
        intervalsec = self.parameterAsInt(parameters, self.INTERVALSEC, context)
        
        if lyr_polygons.sourceCrs() != lyr_points.sourceCrs():
            reproj = processing.run('native:reprojectlayer', {'INPUT': lyr_points, 'TARGET_CRS': lyr_polygons.sourceCrs(), 'OUTPUT': 'memory:Reprojected'})
            lyr_points = reproj['OUTPUT']
        
        fields = lyr_polygons.fields()
        fields.append(QgsField('from_datetime', QVariant.DateTime))
        fields.append(QgsField('to_datetime', QVariant.DateTime))
        fields.append(QgsField('pointcount', QVariant.Int, len=0))
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, lyr_polygons.wkbType(),
                                               lyr_polygons.sourceCrs())
        
        start_date = datetime.strptime(start_date_string, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(end_date_string, '%Y-%m-%d %H:%M:%S')
        total_seconds = int((end_date - start_date).total_seconds())
        idx_points = QgsSpatialIndex(lyr_points.getFeatures())
        
        required_iterations = math.ceil(total_seconds / intervalsec) 
        total = 100.0 / (lyr_polygons.featureCount() * required_iterations) if lyr_polygons.featureCount() else 0
        current = 0
        
        for current_interval in range(0,total_seconds,intervalsec): 
            current_start_datetime = start_date + timedelta(seconds = current_interval)
            current_end_datetime = (start_date + timedelta(seconds = current_interval+intervalsec) - timedelta(seconds = 1))
            for polygon in lyr_polygons.getFeatures():
                current += 1
                new_feat = QgsFeature(fields)
                new_feat.setGeometry(polygon.geometry())
                idx = 0
                for attr in polygon.attributes():
                    new_feat[idx] = attr
                    idx += 1
                new_feat['from_datetime'] = current_start_datetime.strftime('%Y-%m-%d %H:%M:%S')
                new_feat['to_datetime'] = current_end_datetime.strftime('%Y-%m-%d %H:%M:%S')
                new_feat['pointcount'] = 0
                for pointid in idx_points.intersects(polygon.geometry().boundingBox()):
                    point = lyr_points.getFeature(pointid)
                    if feedback.isCanceled():
                        break
                    if point[fld_time] >= current_start_datetime and point[fld_time] <= current_end_datetime:
                        if point.geometry().intersects(polygon.geometry()):
                            new_feat['pointcount'] += 1
                            idx_points.deleteFeature(point) # dont count a point twice, removing it from the index speeds up the code around 25%
                        
                if feedback.isCanceled():
                    break
                    
                sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
                feedback.setProgress(int(current * total))
                
        return {self.OUTPUT: dest_id} # Return result of algorithm
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CountPointsInPolygonByTime()

    def name(self):
        return 'CountPointsInPolygonByTime'

    def displayName(self):
        return self.tr('Count Points in Polygon by Datetime')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr('This Algorithm counts points in polygons by a given datetime condition')