import gzip
import binascii
import os

from galaxy.datatypes.multifile import CompositeMultifile
from galaxy.datatypes import data
from galaxy.datatypes.binary import Binary
from galaxy.datatypes.images import Html
from galaxy.datatypes.metadata import MetadataElement
from galaxy.datatypes.util.image_util import *
from urllib import urlencode
from galaxy import eggs


try:
    import dicom as dcm
except:
    try:
        eggs.require( "pydicom" )
        import dicom as dcm
    except:
        dcm = None

try:
    import nibabel as nib
except:
    try:
        eggs.require( "nibabel" )
        import nibabel as nib
    except:
        nib = None

log = logging.getLogger(__name__)


class Dicom(CompositeMultifile):
    file_ext = "dcm"
    is_binary = False
    allow_datatype_change = False

    MetadataElement(name="Modality", desc="Modality", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="Manufacturer", desc="Manufacturer", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="ManufacturerModelName", desc="Manufacturer Model Name", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="Modality", desc="Modality", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="AccessionNumber", desc="Accession Number", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="AcquisitionDate", desc="Acquisition Date", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="PatientID", desc="Patient ID", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="PatientName", desc="Patient Name", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="SeriesNumber", desc="Series Number", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="StudyID", desc="Study ID", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)

    def set_peek(self, dataset, is_multi_byte=False):
        if not dataset.dataset.purged:
            peek = 'DICOM'
            if dataset.metadata.Modality is not None:
                peek += ' ({modality})'.format(
                    modality=dataset.metadata.Modality)
            if dataset.metadata.PatientName is not None:
                peek += ' {pacient_name}'.format(
                    pacient_name=dataset.metadata.PatientName)
            dataset.peek = peek
        else:
            dataset.peek = 'file does not exist'
            dataset.blurb = 'file purged from disk'

    def sniff(self, filename):
        if dcm is not None:
            try:
                dcm.read_file(filename)
                return True
            except:
                return False
        else:
            return False

    def display_peek(self, dataset):
        try:
            return dataset.peek
        except:
            return "DICOM directory (%s)" % (data.nice_size(dataset.get_size()))

    def set_meta(self, dataset, overwrite=True, **kwd):
        CompositeMultifile.set_meta(self, dataset, **kwd)

        if os.path.isdir(dataset.extra_files_path) and dcm is not None:
            try:
                files = os.listdir(dataset.extra_files_path)
                if files:
                    ds = dcm.read_file(os.path.join(dataset.extra_files_path, files[0]))
                    for meta_name, meta_spec in dataset.datatype.metadata_spec.iteritems():
                        log.debug("Metadata {key} = {value}".format(
                            key=meta_name,
                            value=ds.get(meta_name)))
                        setattr(dataset.metadata, meta_name, ds.get(meta_name))
            except:
                pass

    def get_mime(self):
        return 'text/html'

Binary.register_sniffable_binary_format("dcm", "dcm", Dicom)


class Nifti(Html):
    file_ext = "nii.gz"
    is_binary = False
    allow_datatype_change = False
    composite_type = 'auto_primary_file'

    MetadataElement(name="Modality", desc="Modality", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="Manufacturer", desc="Manufacturer", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="ManufacturerModelName", desc="Manufacturer Model Name", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="Modality", desc="Modality", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="AccessionNumber", desc="Accession Number", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="AcquisitionDate", desc="Acquisition Date", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="PatientID", desc="Patient ID", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="PatientName", desc="Patient Name", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="SeriesNumber", desc="Series Number", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="StudyID", desc="Study ID", default=None, set_in_upload=True, readonly=False, visible=True, optional=True)
    MetadataElement(name="base_name", desc="base_name", default="scan", set_in_upload=True, readonly=True, visible=False, optional=True)

    def __init__(self, **kwd):
        Html.__init__(self, **kwd)
        self.add_composite_file('%s.nii.gz', description='NIfTI File', substitute_name_with_metadata='base_name', is_binary=True, optional=False )
        self.add_composite_file('%s.bvec', description='B-Vectors File', substitute_name_with_metadata='base_name', is_binary=False, optional=True )
        self.add_composite_file('%s.bval', description='B-Values File', substitute_name_with_metadata='base_name', is_binary=False, optional=True )

    def generate_primary_file(self, dataset=None):
        rval = ['<html><head><title>NIfTI Galaxy File</title></head><p/>']
        rval.append('<div>This composite dataset is composed of the following files:<p/><ul>')
        for composite_name, composite_file in self.get_composite_files(dataset=dataset).iteritems():
            fn = composite_name
            opt_text = ''
            if composite_file.optional:
                opt_text = ' (optional)'
            if composite_file.get('description'):
                rval.append( '<li><a href="{filename}" type="application/binary">{fn} ({description})</a>{optional}</li>'.format(
                    filename=fn,
                    description=composite_file.get('description'),
                    optional=opt_text))
            else:
                rval.append( '<li><a href="{filename}" type="application/binary">{filename}</a>{optional}</li>'.format(
                    filename=fn,
                    optional=opt_text))
        rval.append('</ul></div></html>')
        return "\n".join(rval)

    def regenerate_primary_file(self,dataset):
        if dataset.name.endswith('.nii.gz'):
            base_name = dataset.name[:-7]
        else:
            base_name = dataset.name

        efp = dataset.extra_files_path
        flist = os.listdir(efp)
        rval = ['<html><head><title>Files for Composite Dataset {name}</title></head><body><p/>Composite {name} contains:<p/><ul>'.format(name=dataset.name)]
        for i, fname in enumerate(flist):
            sfname = os.path.split(fname)[-1]
            display_name = sfname.replace('dataset', base_name)
            rval.append( '<li><a href="{filename}?{encoded_name}">{name}</a></li>'.format(
                filename=sfname,
                encoded_name=urlencode({"display_name": display_name}),
                name=display_name))
        rval.append('</ul></body></html>')
        f = file(dataset.file_name, 'w')
        f.write("\n".join(rval))
        f.write('\n')
        f.close()

    def get_mime(self):
        return 'text/html'

    def init_meta(self, dataset, copy_from=None):
        Html.init_meta(self, dataset, copy_from=copy_from)
        if copy_from is not None:
            base_name = ''
            if hasattr(copy_from.metadata, 'Modality'):
                base_name += copy_from.metadata.Modality
            if hasattr(copy_from.metadata, 'PatientName'):
                base_name += copy_from.metadata.PatientName
            if base_name:
                dataset.metadata.base_name = base_name

    def set_meta(self, dataset, overwrite=True, **kwd):
        Html.set_meta(self, dataset, **kwd)
        self.regenerate_primary_file(dataset)
        return True

    def sniff(self, filename):
        if nib is not None:
            try:
                nib.load(filename)
                return True
            except:
                return False
        else:
            try:
                header = gzip.open(filename).read(4)
                if binascii.b2a_hex(header) == binascii.hexlify('\x5c\x01\x00\x00'):
                    return True
                return False
            except:
                return False

    def set_peek(self, dataset, is_multi_byte=False):
        if not dataset.dataset.purged:
            peek = 'NIfTI'
            if dataset.metadata.Modality is not None:
                peek += ' ({modality})'.format(
                    modality=dataset.metadata.Modality)
            if dataset.metadata.PatientName is not None:
                peek += ' {pacient_name}'.format(
                    pacient_name=dataset.metadata.PatientName)
            dataset.peek = peek
            dataset.blurb = data.nice_size(dataset.get_size())
        else:
            dataset.peek = 'file does not exist'
            dataset.blurb = 'file purged from disk'

    def display_peek(self, dataset):
        try:
            return dataset.peek
        except:
            return "NIfTI file (%s)" % (data.nice_size(dataset.get_size()))

Binary.register_sniffable_binary_format("nii.gz", "nii.gz", Nifti)
