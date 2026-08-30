project('deepdive',
        version: '1.0.1',
        meson_version: '>= 0.50.0')

python = import('python')
py_installation = python.find_installation('python3')

prefix = get_option('prefix')
bindir = join_paths(prefix, get_option('bindir'))
datadir = join_paths(prefix, get_option('datadir'))
pkgdatadir = join_paths(datadir, meson.project_name())
app_id = 'io.github.tanaybhomia.DeepDive'

# Install python files
install_subdir('deepdive', install_dir: pkgdatadir)
install_data('main.py', install_dir: pkgdatadir)

# Create launch script
conf = configuration_data()
conf.set('PYTHON', py_installation.full_path())
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'deepdive.in',
  output: 'deepdive',
  configuration: conf,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x'
)

# Install data (desktop, metainfo, icons)
install_data('data/' + app_id + '.desktop', install_dir: join_paths(datadir, 'applications'))
install_data('data/' + app_id + '.metainfo.xml', install_dir: join_paths(datadir, 'metainfo'))
install_data('docs/assets/images/app-icon.svg',
             rename: app_id + '.svg',
             install_dir: join_paths(datadir, 'icons', 'hicolor', 'scalable', 'apps'))
