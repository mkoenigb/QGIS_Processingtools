# Author: Mario Königbauer
# License: GNU General Public License v3.0

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (Qgis, QgsField, QgsFeature, QgsProcessing, QgsExpression, QgsGeometry, QgsPoint, QgsFields, QgsVectorLayer, QgsProject,
                       QgsFeatureSink, QgsFeatureRequest, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterField, QgsProcessingParameterNumber, QgsProcessingParameterString, QgsProcessingParameterFeatureSource, QgsProcessingParameterEnum)


class NumberOfIntersectionsBetweenPoints(QgsProcessingAlgorithm):
    POSSIBILITY_LYR = 'POSSIBILITY_LYR'
    POSSIBILITY_IDFIELD = 'POSSIBILITY_IDFIELD'
    POSSIBILITY_TYPFIELD = 'POSSIBILITY_TYPFIELD'
    POSSIBILITY_POLYGONIDFIELD = 'POSSIBILITY_POLYGONIDFIELD'
    STOP_LYR = 'STOP_LYR'
    STOP_IDFIELD = 'STOP_IDFIELD'
    STOP_TYPFIELD = 'STOP_TYPFIELD'
    STOP_POLYGONIDFIELD = 'STOP_POLYGONIDFIELD'
    LINES_LYR = 'LINES_LYR'
    MAXDISTANCE = 'MAXDISTANCE'
    EXCLUDETYPA = 'EXCLUDETYPA'
    EXCLUDETYPB = 'EXCLUDETYPB'
    PRIOA = 'PRIOA'
    PRIOB = 'PRIOB'
    PRIOC = 'PRIOC'
    PRIOD = 'PRIOD'
    PRIOE = 'PRIOE'
    PRIOF = 'PRIOF'
    PRIOG = 'PRIOG'
    OPERATION = 'OPERATION'
    OUTPUTLINES = 'OUTPUTLINES'

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STOP_LYR, self.tr('Source'), [QgsProcessing.TypeVectorPoint],'Stops'))
        self.addParameter(
            QgsProcessingParameterField(
                self.STOP_IDFIELD, self.tr('Unique ID Field of Source Layer (Number)'),'stopid','STOP_LYR',0))      
        self.addParameter(
            QgsProcessingParameterField(
                self.STOP_TYPFIELD, self.tr('VHT Typ Field of Source Layer (String)'),'stoptyp','STOP_LYR',1))  
        #self.addParameter(
        #    QgsProcessingParameterField(
        #        self.STOP_POLYGONIDFIELD, self.tr('Polygon ID Field of Source Layer (Any, but same as Matching Polygon ID Field)'),'polygonid','STOP_LYR'))  
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POSSIBILITY_LYR, self.tr('Possibilities'), [QgsProcessing.TypeVectorPoint],'possibilities'))
        self.addParameter(
            QgsProcessingParameterField(
                self.POSSIBILITY_IDFIELD, self.tr('Unique Possibility ID Field (Number, should have a different name than Source ID field)'),'possibilityid','POSSIBILITY_LYR',0))
        self.addParameter(
            QgsProcessingParameterField(
                self.POSSIBILITY_TYPFIELD, self.tr('VHT Typ Field of Possibilities (String, should have a different name than Source Typ field'),'posstyp','POSSIBILITY_LYR',1))
        #self.addParameter(
        #    QgsProcessingParameterField(
        #        self.POSSIBILITY_POLYGONIDFIELD, self.tr('Polygon ID Field of Possibilities Layer (Any, but same as Source Polygon ID Field)'),'polygonid','POSSIBILITY_LYR'))  
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINES_LYR, self.tr('Intersection Lines'), [QgsProcessing.TypeVectorLine],'LinesTest'))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAXDISTANCE, self.tr('Maxium Distance'), defaultValue = 125))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOA, self.tr('Prio 1 Typ'), defaultValue = 'Einfahrt', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOB, self.tr('Prio 2 Typ'), defaultValue = 'Kreuzung', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOC, self.tr('Prio 3 Typ'), defaultValue = '', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOD, self.tr('Prio 4 Typ'), defaultValue = '', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOE, self.tr('Prio 5 Typ'), defaultValue = '', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOF, self.tr('Prio 6 Typ'), defaultValue = '', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.PRIOG, self.tr('Prio 7 Typ'), defaultValue = '', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.EXCLUDETYPA, self.tr('Exclude Typ 1'), defaultValue = 'nichts', optional = 1))
        self.addParameter(
            QgsProcessingParameterString(
                self.EXCLUDETYPB, self.tr('Exclude Typ 2'), defaultValue = '', optional = 1))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OPERATION, self.tr('Remove ... number of intersections'), ['even','odd'],0,'even'))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUTLINES, self.tr('Output Lines'), QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        # Get Parameters
        possibility_layer = self.parameterAsSource(parameters, self.POSSIBILITY_LYR, context)
        possibility_idfield = self.parameterAsFields(parameters, self.POSSIBILITY_IDFIELD, context)
        possibility_typfield = self.parameterAsFields(parameters, self.POSSIBILITY_TYPFIELD, context)
        stop_layer = self.parameterAsSource(parameters, self.STOP_LYR, context)
        stop_idfield = self.parameterAsFields(parameters, self.STOP_IDFIELD, context)
        stop_typfield = self.parameterAsFields(parameters, self.STOP_TYPFIELD, context)
        lines_layer = self.parameterAsSource(parameters, self.LINES_LYR, context)
        maxdistance = self.parameterAsDouble(parameters, self.MAXDISTANCE, context)
        prio1 = self.parameterAsString(parameters, self.PRIOA, context)
        prio2 = self.parameterAsString(parameters, self.PRIOB, context)
        prio3 = self.parameterAsString(parameters, self.PRIOC, context)
        prio4 = self.parameterAsString(parameters, self.PRIOD, context)
        prio5 = self.parameterAsString(parameters, self.PRIOE, context)
        prio6 = self.parameterAsString(parameters, self.PRIOF, context)
        prio7 = self.parameterAsString(parameters, self.PRIOG, context)
        excl1 = self.parameterAsString(parameters, self.EXCLUDETYPA, context)
        excl2 = self.parameterAsString(parameters, self.EXCLUDETYPB, context)
        operation = self.parameterAsString(parameters, self.OPERATION, context)
        operationlist = [' == ',' != ']
        expressionoperator = str(operationlist[int(operation[0])])        

        #if possibility_idfield == stop_idfield:
        #    iface.messageBar().pushMessage("Error!", "ID Felder haben die gleichen Namen", level=Qgis.Critical, duration=9)
        #if possibility_typfield == stop_typfield:
        #    iface.messageBar().pushMessage("Error!", "Typ Felder haben die gleichen Namen", level=Qgis.Critical, duration=9)
        
        fields = QgsFields()
        fields.append(QgsField("possibility_id", QVariant.Int))
        fields.append(QgsField("possibility_typ", QVariant.String))
        fields.append(QgsField("possibility_priority", QVariant.Int))
        fields.append(QgsField("stop_id", QVariant.Int))
        fields.append(QgsField("stop_typ", QVariant.String))          
        fields.append(QgsField("line_length", QVariant.Double, len=20, prec=5))
        fields.append(QgsField("n_intersections", QVariant.Int))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUTLINES, context,
                                               fields, lines_layer.wkbType(),
                                               lines_layer.sourceCrs())
        print(lines_layer.sourceCrs().authid())
        #Memorylayer_VL = QgsVectorLayer(str('LineString'), "tmp_lines", "memory")        
        Memorylayer_VL = QgsVectorLayer(str('LineString?crs=')+str(lines_layer.sourceCrs().authid()), "tmp_lines", "memory")
        Memorylayer_PR = Memorylayer_VL.dataProvider()
        Memorylayer_VL.startEditing()
        Memorylayer_PR.addAttributes([QgsField("possid", QVariant.Int),QgsField("posstyp", QVariant.String),QgsField("possprio", QVariant.Int),QgsField("stopid", QVariant.Int),QgsField("stoptyp", QVariant.String),QgsField("line_length", QVariant.Double, len=20, prec=5),QgsField("n_intersections", QVariant.Int)])
        Memorylayer_VL.updateFields()
        #crs = Memorylayer_VL.crs()
        #crs.createFromId(25832)
        #Memorylayer_VL.setCrs(crs)
        
        
        # iterate over stop features
        for stop_feat in stop_layer.getFeatures():
            point1 = QgsPoint(stop_feat.geometry().asPoint())
            for source_feat in possibility_layer.getFeatures():
                point2 = QgsPoint(source_feat.geometry().asPoint())
                temp_feat = QgsFeature(fields)
                temp_feat.setGeometry(QgsGeometry.fromPolyline([point1, point2])) 
                temp_feat["stop_id"] = stop_feat[stop_idfield[0]] 
                temp_feat["stop_typ"] = stop_feat[stop_typfield[0]] 
                temp_feat["possibility_id"] = source_feat[possibility_idfield[0]] 
                temp_feat["possibility_typ"] = source_feat[possibility_typfield[0]] 
                temp_feat["possibility_priority"] = 0
                temp_feat["line_length"] = temp_feat.geometry().length() 
                temp_feat["n_intersections"] = 0
                #temp_feat.setAttributes([source_feat[possibility_idfield[0]],source_feat[possibility_typfield[0]],stop_feat[stop_idfield[0]],stop_feat[stop_typfield[0]],temp_feat.geometry().length(),-1])
                #temp_feat.setAttributes([temp_feat.geometry().length(),-1])
                Memorylayer_PR.addFeature(temp_feat)
                Memorylayer_VL.updateFields()
        Memorylayer_VL.commitChanges()
        
        # remove lines which are too long
        print('Fields: ' + str(Memorylayer_VL.fields().count()))
        print('Vorher: ' + str(Memorylayer_VL.featureCount()))
        dfeats = [] # Create empty list of features to delete later
        for tmp_line_feat in Memorylayer_VL.getFeatures():
            #print(str(tmp_line_feat.attributes()[0]) + ' ' + str(tmp_line_feat.attributes()[1])+ ' '+ str(tmp_line_feat.attributes()[2])+ ' '+ str(tmp_line_feat.attributes()[3])+ ' '+ str(tmp_line_feat.attributes()[4])+ ' '+ str(tmp_line_feat.attributes()[5])+ ' ')
            if tmp_line_feat.geometry().length() > maxdistance:
                dfeats.append(tmp_line_feat.id())
            if tmp_line_feat.geometry().length() < 1:
                dfeats.append(tmp_line_feat.id())
        Memorylayer_PR.deleteFeatures(dfeats)
        Memorylayer_VL.commitChanges()
        print('Nachher: ' + str(Memorylayer_VL.featureCount()))
        
        # remove excludetyps
        dfeats10 = []
        for tmp_line_feat in Memorylayer_VL.getFeatures():
            if tmp_line_feat.attributes()[1] == excl1:
                dfeats10.append(tmp_line_feat.id())
            elif tmp_line_feat.attributes()[1] == excl2:
                dfeats10.append(tmp_line_feat.id())
            else:
                None
        Memorylayer_PR.deleteFeatures(dfeats10)
        Memorylayer_VL.commitChanges()
        
        # count intersections
        for tmp_line_feat in Memorylayer_VL.getFeatures():
            counter = 0
            for streets in lines_layer.getFeatures():                
                if tmp_line_feat.geometry().intersects(streets.geometry()):
                    counter = counter + 1
                attr = {6:counter}
                Memorylayer_PR.changeAttributeValues({ tmp_line_feat.id() : attr })
        Memorylayer_VL.commitChanges()  
        
        # remove unwanted number of intersections
        dfeats2 = []
        if expressionoperator == ' == ': #take this loop to remove even number of intersections                    
            for tmp_line_feat in Memorylayer_VL.getFeatures():
                if (tmp_line_feat.attributes()[6] % 2) == 0:
                    dfeats2.append(tmp_line_feat.id())
        if expressionoperator == ' != ': #take this loop to remove uneven number of intersections 
            for tmp_line_feat in Memorylayer_VL.getFeatures():
                if (tmp_line_feat.attributes()[6] % 2) != 0: 
                    dfeats2.append(tmp_line_feat.id())
        Memorylayer_PR.deleteFeatures(dfeats2)
        Memorylayer_VL.commitChanges()
        
        # add priority numbers
        for tmp_line_feat in Memorylayer_VL.getFeatures():
            if tmp_line_feat.attributes()[1] == prio1:
                attr = {2:1}
            elif tmp_line_feat.attributes()[1] == prio2:
                attr = {2:2}
            elif tmp_line_feat.attributes()[1] == prio3:
                attr = {2:3}
            elif tmp_line_feat.attributes()[1] == prio4:
                attr = {2:4}
            elif tmp_line_feat.attributes()[1] == prio5:
                attr = {2:5}
            elif tmp_line_feat.attributes()[1] == prio6:
                attr = {2:6}
            elif tmp_line_feat.attributes()[1] == prio7:
                attr = {2:7}
            else:
                attr = {2:9}
            Memorylayer_PR.changeAttributeValues({ tmp_line_feat.id() : attr })    
        Memorylayer_VL.commitChanges()
        
        # check for priorities and remove unwanted
        dfeats3 = []
        vals = {}
        for tmp_line_feat in Memorylayer_VL.getFeatures(): # populate dict
            if tmp_line_feat.attributes()[3] not in vals:
                vals[tmp_line_feat.attributes()[3]] = [tmp_line_feat[2]]
            else:
                vals[tmp_line_feat.attributes()[3]].append(tmp_line_feat[2])
        for key, value in vals.items(): # find minimum priority
            vals[key] = min(value)
        for tmp_line_feat in Memorylayer_VL.getFeatures(): # delete lower prios
            k = tmp_line_feat[3]
            if tmp_line_feat[2] != vals[k]:
                dfeats3.append(tmp_line_feat.id())
            else:
                None
        Memorylayer_PR.deleteFeatures(dfeats3) 
        Memorylayer_VL.commitChanges()        
        
        # in case there are several prios of same type for one stop, lets keep the nearest
        dfeats4 = []
        vals2 = {}
        for tmp_line_feat in Memorylayer_VL.getFeatures(): # populate dict
            if tmp_line_feat.attributes()[3] not in vals2:
                vals2[tmp_line_feat.attributes()[3]] = [tmp_line_feat[5]]
            else:
                vals2[tmp_line_feat.attributes()[3]].append(tmp_line_feat[5])
        for key, value in vals2.items(): # find minimum priority
            vals2[key] = min(value)
        for tmp_line_feat in Memorylayer_VL.getFeatures(): # delete farther distances
            l = tmp_line_feat[3]
            if tmp_line_feat[5] != vals2[l]:
                dfeats4.append(tmp_line_feat.id())
            else:
                None
        Memorylayer_PR.deleteFeatures(dfeats4)
        Memorylayer_VL.commitChanges()
        
        # create output
        for tmp_line_feat in Memorylayer_VL.getFeatures():
            new_feat = QgsFeature(fields)
            new_feat.setGeometry(tmp_line_feat.geometry()) 
            new_feat["stop_id"] = tmp_line_feat.attributes()[3]   
            new_feat["stop_typ"] = tmp_line_feat.attributes()[4]           
            new_feat["possibility_id"] = tmp_line_feat.attributes()[0]
            new_feat["possibility_typ"] = tmp_line_feat.attributes()[1]
            new_feat["possibility_priority"] = tmp_line_feat.attributes()[2]
            new_feat["line_length"] = tmp_line_feat.attributes()[5] 
            new_feat["n_intersections"] = tmp_line_feat.attributes()[6]
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert)    
        
        
        return {self.OUTPUTLINES: dest_id}


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return NumberOfIntersectionsBetweenPoints()

    def name(self):
        return 'NumberOfIntersectionsBetweenPoints'

    def displayName(self):
        return self.tr('Number Of Intersections Between Points')

    def group(self):
        return self.tr('FROM GISSE')

    def groupId(self):
        return 'from_gisse'

    def shortHelpString(self):
        return self.tr('...')