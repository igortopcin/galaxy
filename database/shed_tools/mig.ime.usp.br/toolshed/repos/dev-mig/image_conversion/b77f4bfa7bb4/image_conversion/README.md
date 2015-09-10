Image conversion tools
======================

DICOM to NIfTI
--------------

This tool converts a DICOM folder (i.e. a composite dataset in Galaxy) into a single NIfTI file. It also produces two separate text files: bval and bvec (see below).

Difusion Data
-------------

Diffusion sequences are sensitive to the random spontaneous motion of water molecules. This movement is
anisotropic in fiber bundles - in other words it preferentially moves up and down the fibers whereas motion
across the fiber is constrained. Diffusion tensor imaging (DTI) use different gradient directions so that
different images are sensitive to specific directions. In order to process this data with medINRIA or FSL, you
need to extract the diffusion direction information as well as the images. For these images, dcm2nii will
attempt to generate .bvec and .bval text files. This information is extracted from the DICOM header (for Siemens
data the software attempts to read the "B_value" and "DiffusionGradientDirection" fields from the CSA header).
