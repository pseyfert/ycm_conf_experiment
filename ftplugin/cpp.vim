" Set makeprg for LHCb projects
" Author:      Paul Seyfert
" Version:     0.0.0
" WebPage:     https://github.com/pseyfert/ycm_conf_experiment.git
" Description: Sets the makeprg variable for LHCb projects
" License:     GPL v3, see LICENSE for more details.

let s:save_cpo = &cpo
set cpo&vim

let g:lhcb_ycm_util = expand('<sfile>:p:h:h') . '/ycm_conf_utils/lhcb.py'
if has('python3')
  execute ':py3file ' . g:lhcb_ycm_util
  execute ':python3 import vim'
  " https://vim.fandom.com/wiki/Get_the_name_of_the_current_file
  execute ':python3 db, common = getdb("' . expand('%:p') . '", None)'
  execute ':python3 if db is not None: vim.command("let &makeprg=\"ninja -C {}\"".format(os.path.dirname(db).decode()))'
elseif has('python3')
  execute ':pyfile ' . g:lhcb_ycm_util
  execute ':python import vim'
  " https://vim.fandom.com/wiki/Get_the_name_of_the_current_file
  execute ':python db, common = getdb("' . expand('%:p') . '", None)'
  execute ':python if db is not None: vim.command("let &makeprg=\"ninja -C {}\"".format(os.path.dirname(db).decode()))'
endif

let &cpo = s:save_cpo
unlet s:save_cpo
