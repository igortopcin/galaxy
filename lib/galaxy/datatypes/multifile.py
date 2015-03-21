import data
import logging
import os
from urllib import urlencode


log = logging.getLogger(__name__)


class CompositeMultifile(data.Data):
    file_ext = 'multi'
    composite_type = 'multifile'
    blurb = 'Composite multifile'

    def split(cls, input_datasets, subdir_generator_function, split_params):
        """
        Split the input composite dataset into individual files in task
        directories.
        """
        if split_params is None:
            return

        # only one split_mode is accepted
        if split_params['split_mode'] != 'from_composite':
            raise Exception('Unsupported split mode %s. Use only from_composite as split mode.' % split_params['split_mode'])

        # Test if datasets are eligible for multifile splitting (similar number of files in datasets)
        amount = {}
        filetypes = {}
        for in_data in input_datasets:
            try:
                in_files = os.listdir(in_data.extra_files_path)
            except OSError:
                in_files = [in_data]
                log.debug('Single file fed to splitting function. Faking a'
                          ' composite file type by creating an appropriately'
                          ' named softlink in an extra_files_path folder.')
                os.makedirs(in_data.extra_files_path)
                fn = os.path.basename(in_data.file_name)
                os.symlink(in_data.file_name,
                           os.path.join(in_data.extra_files_path, fn))
                in_files = os.listdir(in_data.extra_files_path)

            amount[len(in_files)] = 1
            filetypes[in_data.file_name] = {}
            for in_file in in_files:
                if '.' not in in_file:
                    filetypes[in_data.file_name][''] = 1
                else:
                    ext = in_file.split('.')[-1]
                    filetypes[in_data.file_name][ext] = 1
            assert len(filetypes[in_data.file_name].keys()) == 1, Exception('Different filetypes found in composite file list. Cannot split.')

        assert len(amount.keys()) == 1, Exception('Different number of files are contained in the different dataset.')
        # Split files
        try:
            # Take one file per composite dataset, and put it in a new task directory
            for filenum in range(amount.keys()[0]):
                part_dir = subdir_generator_function()
                for in_data in input_datasets:
                    members = os.listdir(in_data.extra_files_path)
                    member = members[filenum]
                    part_path = os.path.join(
                        part_dir,
                        os.path.basename(in_data.file_name))
                    os.symlink(os.path.join(in_data.extra_files_path, member),
                               part_path)
        except Exception:
            raise
    split = classmethod(split)

    def merge(split_files, output_dataset, output_filename, newnames=None):
        """
        Merges result files from task directories back into a composite
        dataset's extra_files_path directory.
        """
        with open(output_filename, 'w') as fp:
            fp.write('Composite dataset')
        os.makedirs(output_dataset.extra_files_path)
        try:
            for i, in_file in enumerate(split_files):
                if not newnames:
                    filename, old_parentdir = os.path.split(in_file)[-1], os.path.split(os.path.split(in_file)[0])[-1]
                    if 'task_' not in old_parentdir:
                        raise Exception, 'Files named incorrectly and no new names supplied, cannot merge.'
                else:
                    filename = newnames[i]
                os.rename(in_file, os.path.join(output_dataset.extra_files_path, filename))
        except Exception:
            raise

    merge = staticmethod(merge)

    def set_peek(self, dataset, is_multi_byte=True):
        """Set the peek and blurb text"""
        dataset.peek = '\n'.join(sorted(os.listdir(dataset.extra_files_path)))
        dataset.blurb = self.blurb

    def generate_primary_file(self, dataset=None):
        if dataset.name.endswith('.nii.gz'):
            base_name = dataset.name[:-7]
        else:
            base_name = dataset.name

        flist = os.listdir(dataset.extra_files_path)
        content = ['<html><body><p/>Files in {name}:<p/><ul>'.format(name=dataset.name)]
        for i, fname in enumerate(flist):
            sfname = os.path.split(fname)[-1]
            display_name = sfname.replace('dataset', base_name)
            content.append( '<li><a href="{filename}?{encoded_name}">{name}</a></li>'.format(
                filename=sfname,
                encoded_name=urlencode({"display_name": display_name}),
                name=display_name))
        content.append('</ul></body></html>')
        return '\n'.join(content) + '\n'

    def regenerate_primary_file(self, dataset):
        content = self.generate_primary_file(dataset)
        f = file(dataset.file_name, 'w')
        f.write(content)
        f.close()

    def set_meta(self, dataset, overwrite=True, **kwd):
        data.Data.set_meta(self, dataset, **kwd)
        self.regenerate_primary_file(dataset)
        return True

    def get_mime(self):
        """Returns the mime type of the datatype"""
        return 'text/html'


class MultiText(data.Text, CompositeMultifile):
    file_ext = 'mtxt'
    blurb = 'Composite multi text files'
