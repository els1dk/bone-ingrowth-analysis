import logging
import os
from typing import Annotated

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode

#
# BoneIngrowthAnalysis
#


class BoneIngrowthAnalysis(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("BoneIngrowthAnalysis")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#BoneIngrowthAnalysis">module documentation</a>.
""")
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="BoneIngrowthAnalysis",
        sampleName="BoneIngrowthAnalysis1",
        thumbnailFileName=os.path.join(iconsPath, "BoneIngrowthAnalysis1.png"),
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="BoneIngrowthAnalysis1.nrrd",
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        nodeNames="BoneIngrowthAnalysis1",
    )

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="BoneIngrowthAnalysis",
        sampleName="BoneIngrowthAnalysis2",
        thumbnailFileName=os.path.join(iconsPath, "BoneIngrowthAnalysis2.png"),
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="BoneIngrowthAnalysis2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        nodeNames="BoneIngrowthAnalysis2",
    )


#
# BoneIngrowthAnalysisParameterNode
#


@parameterNodeWrapper
class BoneIngrowthAnalysisParameterNode:
    """
    The parameters needed by module.

    inputVolume - The CT volume to analyze.
    cupSegmentation - The segmentation of the acetabular cup.
    boneThreshold - The HU value above which a voxel is considered bone.
    metalThreshold - The HU value above which a voxel is considered metal/prosthesis.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    cupSegmentation: vtkMRMLSegmentationNode
    boneThreshold: Annotated[float, WithinRange(-1000, 3000)] = 300
    metalThreshold: Annotated[float, WithinRange(0, 5000)] = 2500


#
# BoneIngrowthAnalysisWidget
#


class BoneIngrowthAnalysisWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)

        uiWidget = slicer.util.loadUI(self.resourcePath("UI/BoneIngrowthAnalysis.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        uiWidget.setMRMLScene(slicer.mrmlScene)
        self.ui.cupSegmentationSelector.setMRMLScene(slicer.mrmlScene)

        self.logic = BoneIngrowthAnalysisLogic()

        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        self.initializeParameterNode()

    def cleanup(self) -> None:
        self.removeObservers()

    def enter(self) -> None:
        self.initializeParameterNode()

    def exit(self) -> None:
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        self.setParameterNode(self.logic.getParameterNode())

        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: BoneIngrowthAnalysisParameterNode | None) -> None:
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.cupSegmentation:
            self.ui.applyButton.toolTip = _("Compute bone ingrowth analysis")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input volume and cup segmentation")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            self.logic.process(
                self._parameterNode.inputVolume,
                self._parameterNode.cupSegmentation,
                self._parameterNode.boneThreshold,
                self._parameterNode.metalThreshold,
            )


#
# BoneIngrowthAnalysisLogic
#


class BoneIngrowthAnalysisLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return BoneIngrowthAnalysisParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                cupSegmentation: vtkMRMLSegmentationNode,
                boneThreshold: float,
                metalThreshold: float) -> None:
        """
        Identify the acetabular cup(s) within the metal segmentation using
        connected-component analysis and shape-based filtering (z-extent and
        voxel count), not hardcoded object ordering, per project brief.
        Writes the result into a new segment called "CupOnly" so the original
        full metal segmentation is not destroyed. Then classifies the cup
        surface into bone-facing vs rim (Section 6.2).
        """
        if not inputVolume or not cupSegmentation:
            raise ValueError("Input volume or cup segmentation is invalid")

        import numpy as np
        import scipy.ndimage as ndi
        import time

        startTime = time.time()
        print("Processing started")

        segmentation = cupSegmentation.GetSegmentation()
        numSegments = segmentation.GetNumberOfSegments()
        if numSegments == 0:
            raise ValueError("No segments found in cup segmentation")
        segmentId = segmentation.GetNthSegmentID(0)

        segArray = slicer.util.arrayFromSegmentBinaryLabelmap(cupSegmentation, segmentId)
        labeled, numComponents = ndi.label(segArray)
        print(f"Found {numComponents} connected components in metal segmentation")

        candidateCups = []
        for i in range(1, numComponents + 1):
            coords = np.argwhere(labeled == i)
            voxelCount = coords.shape[0]
            if voxelCount < 100:
                continue
            bbox = coords.max(axis=0) - coords.min(axis=0)
            zExtent = bbox[0]
            print(f"  Component {i}: voxels={voxelCount}, zExtent={zExtent}")
            if zExtent < 100 and voxelCount > 8000:
                candidateCups.append(i)

        print(f"Candidate cup components: {candidateCups}")

        if len(candidateCups) == 0:
            raise ValueError("No cup-like components found - check thresholds")

        cupOnlyArray = np.isin(labeled, candidateCups).astype(np.uint8)

        cupSegmentId = segmentation.GetSegmentIdBySegmentName("CupOnly")
        if not cupSegmentId:
            cupSegmentId = segmentation.AddEmptySegment("CupOnly")
        slicer.util.updateSegmentBinaryLabelmapFromArray(cupOnlyArray, cupSegmentation, cupSegmentId)

        self.identifyCupSurfaceZones(cupSegmentation)

        stopTime = time.time()
        print(f"Processing completed in {stopTime-startTime:.2f} seconds")

    def identifyCupSurfaceZones(self, cupSegmentation, alignmentThreshold=0.317):
        """
        For each connected cup component in the "CupOnly" segment, converts
        it to a surface mesh, fits a sphere, and classifies each mesh point
        as bone-facing or rim/opening based on direction alignment relative
        to the sphere's true center (Section 6.2).
        """
        import numpy as np

        segmentation = cupSegmentation.GetSegmentation()
        cupSegmentId = segmentation.GetSegmentIdBySegmentName("CupOnly")
        if not cupSegmentId and segmentation.GetSegment("CupOnly"):
            cupSegmentId = "CupOnly"
        if not cupSegmentId:
            raise ValueError("CupOnly segment not found - run cup identification first")

        cupSegmentation.CreateClosedSurfaceRepresentation()
        polyData = vtk.vtkPolyData()
        cupSegmentation.GetClosedSurfaceRepresentation(cupSegmentId, polyData)

        connectivityFilter = vtk.vtkPolyDataConnectivityFilter()
        connectivityFilter.SetInputData(polyData)
        connectivityFilter.SetExtractionModeToAllRegions()
        connectivityFilter.ColorRegionsOn()
        connectivityFilter.Update()

        labeledPolyData = connectivityFilter.GetOutput()
        numRegions = connectivityFilter.GetNumberOfExtractedRegions()
        print(f"Found {numRegions} separate cup regions")

        regionArray = labeledPolyData.GetPointData().GetArray("RegionId")
        regionIds = np.array([regionArray.GetValue(i) for i in range(regionArray.GetNumberOfTuples())])
        allPoints = np.array([labeledPolyData.GetPoint(i) for i in range(labeledPolyData.GetNumberOfPoints())])

        results = []
        for regionIndex in range(numRegions):
            regionPoints = allPoints[regionIds == regionIndex]
            if regionPoints.shape[0] < 50:
                continue

            center, radius = self.fitSphere(regionPoints)

            directions = (regionPoints - center) / radius
            meanDirection = directions.mean(axis=0)
            meanDirection = meanDirection / np.linalg.norm(meanDirection)
            alignmentScore = np.dot(directions, meanDirection)

            boneFacingMask = alignmentScore > alignmentThreshold
            boneFacingPoints = regionPoints[boneFacingMask]
            rimPoints = regionPoints[~boneFacingMask]

            print(f"Cup region {regionIndex}: radius={radius:.2f}mm, "
                  f"bone-facing={boneFacingPoints.shape[0]}, rim={rimPoints.shape[0]}")

            self.createPointCloudModel(boneFacingPoints, f"BoneFacing_Cup{regionIndex}", (1, 0, 0))
            self.createPointCloudModel(rimPoints, f"Rim_Cup{regionIndex}", (0, 0, 1))

            results.append({
                'center': center,
                'radius': radius,
                'boneFacingPoints': boneFacingPoints,
                'rimPoints': rimPoints,
            })

        return results

    @staticmethod
    def fitSphere(points):
        """Least-squares fit of a sphere to a set of 3D points. Returns (center, radius)."""
        import numpy as np
        A = np.hstack([2 * points, np.ones((points.shape[0], 1))])
        b = np.sum(points ** 2, axis=1)
        result, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        center = result[:3]
        radius = np.sqrt(result[3] + np.sum(center ** 2))
        return center, radius

    @staticmethod
    def createPointCloudModel(pointsArray, name, color):
        """Creates a visible point-cloud model node from a numpy array of 3D points."""
        vtkPoints = vtk.vtkPoints()
        for p in pointsArray:
            vtkPoints.InsertNextPoint(p)
        poly = vtk.vtkPolyData()
        poly.SetPoints(vtkPoints)
        glyphFilter = vtk.vtkVertexGlyphFilter()
        glyphFilter.SetInputData(poly)
        glyphFilter.Update()

        existing = slicer.mrmlScene.GetFirstNodeByName(name)
        if existing:
            slicer.mrmlScene.RemoveNode(existing)

        node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode', name)
        node.SetAndObservePolyData(glyphFilter.GetOutput())
        node.CreateDefaultDisplayNodes()
        node.GetDisplayNode().SetColor(*color)
        node.GetDisplayNode().SetPointSize(4)
        node.GetDisplayNode().SetVisibility(True)
        return node


#
# BoneIngrowthAnalysisTest
#


class BoneIngrowthAnalysisTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        self.setUp()
        self.delayDisplay("Skipping legacy sample-data test (not applicable to this module).")