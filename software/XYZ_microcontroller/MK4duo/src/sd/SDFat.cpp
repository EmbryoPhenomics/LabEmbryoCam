/**
 * MK4duo Firmware for 3D Printer, Laser and CNC
 *
 * Based on Marlin, Sprinter and grbl
 * Copyright (C) 2011 Camiel Gubbels / Erik van der Zalm
 * Copyright (C) 2013 Alberto Cotronei @MagoKimbra
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 */

/**
 * Arduino SdFat Library
 * Copyright (C) 2012 by William Greiman
 *
 * This file is part of the Arduino SdFat Library
 *
 * This Library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This Library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with the Arduino SdFat Library. If not, see
 * <http://www.gnu.org/licenses/>.
 */

#include "../../MK4duo.h"

#if HAS_SD_SUPPORT

#include "Arduino.h"
#include "SDFat.h"

extern int8_t RFstricmp(PGM_P s1, PGM_P s2) {
  while(*s1 && (tolower(*s1) == tolower(*s2)))
    s1++, s2++;
  return (const uint8_t)tolower(*s1) - (const uint8_t)tolower(*s2);
}

extern int8_t RFstrnicmp(PGM_P s1, PGM_P s2, size_t n) {
  while(n--) {
    if(tolower(*s1) != tolower(*s2))
      return (uint8_t)tolower(*s1) - (uint8_t)tolower(*s2);
    s1++;
    s2++;
  }
  return 0;
}

//------------------------------------------------------------------------------
static void pstrPrintln(PGM_P str) {
  SERIAL_ET(str);
}
//------------------------------------------------------------------------------
/**
 * Initialize an SdFat object.
 *
 * Initializes the SD card, SD volume, and root directory.
 *
 * \param[in] chipSelectPin SD chip select pin. See Sd2Card::init().
 * \param[in] sckRateID value for SPI SCK rate. See Sd2Card::init().
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdFat::begin(uint8_t chipSelectPin, uint8_t sckRateID) {
  return card_.init(sckRateID, chipSelectPin) && vol_.init(&card_) && chdir(1);
}
//------------------------------------------------------------------------------

/** Change a volume's working directory to root
 *
 * Changes the volume's working directory to the SD's root directory.
 * Optionally set the current working directory to the volume's
 * working directory.
 *
 * \param[in] set_cwd Set the current working directory to this volume's
 *  working directory if true.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdFat::chdir(bool set_cwd) {
  if (set_cwd) SdBaseFile::cwd_ = &vwd_;
  if (vwd_.isOpen()) vwd_.close();
  return vwd_.openRoot(&vol_);
}
//------------------------------------------------------------------------------
/** Change a volume's working directory
 *
 * Changes the volume working directory to the \a path subdirectory.
 * Optionally set the current working directory to the volume's
 * working directory.
 *
 * Example: If the volume's working directory is "/DIR", chdir("SUB")
 * will change the volume's working directory from "/DIR" to "/DIR/SUB".
 *
 * If path is "/", the volume's working directory will be changed to the
 * root directory
 *
 * \param[in] path The name of the subdirectory.
 *
 * \param[in] set_cwd Set the current working directory to this volume's
 *  working directory if true.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdFat::chdir(PGM_P path, bool set_cwd) {
  SdBaseFile dir;
  if (path[0] == '/' && path[1] == '\0') return chdir(set_cwd);

  if (!dir.open(&vwd_, path, O_READ)) goto FAIL;
  if (!dir.isDir()) goto FAIL;
  vwd_ = dir;
  if (set_cwd) SdBaseFile::cwd_ = &vwd_;
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Set the current working directory to a volume's working directory.
 *
 * This is useful with multiple SD cards.
 *
 * The current working directory is changed to this volume's working directory.
 *
 * This is like the Windows/DOS \<drive letter>: command.
 */
void SdFat::chvol() {
  SdBaseFile::cwd_ = &vwd_;
}
//------------------------------------------------------------------------------
/** %Print any SD error code and halt. */
void SdFat::errorHalt() {
  errorPrint();
  while (1);
}
//------------------------------------------------------------------------------
/** %Print msg, any SD error code, and halt.
 *
 * \param[in] msg Message to print.
 */
void SdFat::errorHalt(char const* msg) {
  errorPrint(msg);
  while (1);
}
//------------------------------------------------------------------------------
/** %Print msg, any SD error code, and halt.
 *
 * \param[in] msg Message in program space (flash memory) to print.
 */
void SdFat::errorHalt_P(PGM_P msg) {
  errorPrint_P(msg);
  while (1);
}
//------------------------------------------------------------------------------
/** %Print any SD error code. */
void SdFat::errorPrint() {
  if (!card_.errorCode()) return;
  SERIAL_LMV(ER, MSG_SD_ERRORCODE, card_.errorCode());
}
//------------------------------------------------------------------------------
/** %Print msg, any SD error code.
 *
 * \param[in] msg Message to print.
 */
void SdFat::errorPrint(PGM_P msg) {
  SERIAL_LT(ER, msg);
  errorPrint();
}
//------------------------------------------------------------------------------
/** %Print msg, any SD error code.
 *
 * \param[in] msg Message in program space (flash memory) to print.
 */
void SdFat::errorPrint_P(PGM_P msg) {
  SERIAL_LT(ER, msg);
  errorPrint();
}
//------------------------------------------------------------------------------
/**
 * Test for the existence of a file.
 *
 * \param[in] name Name of the file to be tested for.
 *
 * \return true if the file exists else false.
 */
bool SdFat::exists(PGM_P name) {
  return vwd_.exists(name);
}
//------------------------------------------------------------------------------
/** %Print error details and halt after SdFat::init() fails. */
void SdFat::initErrorHalt() {
  initErrorPrint();
  while (1);
}
//------------------------------------------------------------------------------
/**Print message, error details, and halt after SdFat::init() fails.
 *
 * \param[in] msg Message to print.
 */
void SdFat::initErrorHalt(PGM_P msg) {
  SERIAL_LT(ER, msg);
  initErrorHalt();
}
//------------------------------------------------------------------------------
/**Print message, error details, and halt after SdFat::init() fails.
 *
 * \param[in] msg Message in program space (flash memory) to print.
 */
void SdFat::initErrorHalt_P(PGM_P msg) {
  pstrPrintln(msg);
  initErrorHalt();
}
//------------------------------------------------------------------------------
/** Print error details after SdFat::init() fails. */
void SdFat::initErrorPrint() {
  if (card_.errorCode()) {
    pstrPrintln(PSTR("Can't access SD card. Do not reformat."));
    if (card_.errorCode() == SD_CARD_ERROR_CMD0) {
      pstrPrintln(PSTR("No card, wrong chip select pin, or SPI problem?"));
    }
    errorPrint();
  } else if (vol_.fatType() == 0) {
    pstrPrintln(PSTR("Invalid format, reformat SD."));
  } else if (!vwd_.isOpen()) {
    pstrPrintln(PSTR("Can't open root directory."));
  } else {
    pstrPrintln(PSTR("No error found."));
  }
}
//------------------------------------------------------------------------------
/**Print message and error details and halt after SdFat::init() fails.
 *
 * \param[in] msg Message to print.
 */
void SdFat::initErrorPrint(PGM_P msg) {
  SERIAL_LT(ER, msg);
  initErrorPrint();
}
//------------------------------------------------------------------------------
/**Print message and error details after SdFat::init() fails.
 *
 * \param[in] msg Message in program space (flash memory) to print.
 */
void SdFat::initErrorPrint_P(PGM_P msg) {
  pstrPrintln(msg);
  initErrorHalt();
}
//------------------------------------------------------------------------------
/** Make a subdirectory in the volume working directory.
 *
 * \param[in] path A path with a valid 8.3 DOS name for the subdirectory.
 *
 * \param[in] pFlag Create missing parent directories if true.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdFat::mkdir(PGM_P path, bool pFlag) {
  SdBaseFile sub;
  return sub.mkdir(&vwd_, path, pFlag);
}
//------------------------------------------------------------------------------
/** Remove a file from the volume working directory.
*
* \param[in] path A path with a valid 8.3 DOS name for the file.
*
* \return The value one, true, is returned for success and
* the value zero, false, is returned for failure.
*/
bool SdFat::remove(PGM_P path) {
  return SdBaseFile::remove(&vwd_, path);
}
//------------------------------------------------------------------------------
/** Rename a file or subdirectory.
 *
 * \param[in] oldPath Path name to the file or subdirectory to be renamed.
 *
 * \param[in] newPath New path name of the file or subdirectory.
 *
 * The \a newPath object must not exist before the rename call.
 *
 * The file to be renamed must not be open.  The directory entry may be
 * moved and file system corruption could occur if the file is accessed by
 * a file object that was opened before the rename() call.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdFat::rename(PGM_P oldPath, PGM_P newPath) {
  SdBaseFile file;
  if (!file.open(oldPath, O_READ)) return false;
  return file.rename(&vwd_, newPath);
}
//------------------------------------------------------------------------------
/** Remove a subdirectory from the volume's working directory.
 *
 * \param[in] path A path with a valid 8.3 DOS name for the subdirectory.
 *
 * The subdirectory file will be removed only if it is empty.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdFat::rmdir(PGM_P path) {
  SdBaseFile sub;
  if (!sub.open(path, O_READ)) return false;
  return sub.rmdir();
}
//------------------------------------------------------------------------------
/** Truncate a file to a specified length.  The current file position
 * will be maintained if it is less than or equal to \a length otherwise
 * it will be set to end of file.
 *
 * \param[in] path A path with a valid 8.3 DOS name for the file.
 * \param[in] length The desired length for the file.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include file is read only, file is a directory,
 * \a length is greater than the current file size or an I/O error occurs.
 */
bool SdFat::truncate(PGM_P path, uint32_t length) {
  SdBaseFile file;
  if (!file.open(path, O_WRITE)) return false;
  return file.truncate(length);
}

//==============================================================================
// SdBaseFile member functions
//------------------------------------------------------------------------------
// macro for debug
#define DBG_FAIL_MACRO  //  SERIAL_EV(__LINE__)
//------------------------------------------------------------------------------
// pointer to cwd directory
SdBaseFile* SdBaseFile::cwd_ = 0;
// callback function for date/time
void (*SdBaseFile::dateTime_)(uint16_t* date, uint16_t* time) = 0;
//------------------------------------------------------------------------------
// add a cluster to a file
bool SdBaseFile::addCluster() {
  if (!vol_->allocContiguous(1, &curCluster_)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // if first cluster of file link to directory entry
  if (firstCluster_ == 0) {
    firstCluster_ = curCluster_;
    flags_ |= F_FILE_DIR_DIRTY;
  }
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
// Add a cluster to a directory file and zero the cluster.
// return with first block of cluster in the cache
cache_t* SdBaseFile::addDirCluster() {
  uint32_t block;
  cache_t* pc;
  // max folder size
  if (fileSize_ / sizeof(dir_t) >= 0xFFFF) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (!addCluster()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  block = vol_->clusterStartBlock(curCluster_);
  pc = vol_->cacheFetch(block, SdVolume::CACHE_RESERVE_FOR_WRITE);
  if (!pc) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  memset(pc, 0, 512);
  // zero rest of clusters
  for (uint8_t i = 1; i < vol_->blocksPerCluster_; i++) {
    if (!vol_->writeBlock(block + i, pc->data)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  // Increase directory file size by cluster size
  fileSize_ += 512UL*vol_->blocksPerCluster_;
  return pc;

FAIL:
  return 0;
}
//------------------------------------------------------------------------------
// cache a file's directory entry
// return pointer to cached entry or null for failure
dir_t* SdBaseFile::cacheDirEntry(uint8_t action) {
  cache_t* pc;
  pc = vol_->cacheFetch(dirBlock_, action);
  if (!pc) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  return pc->dir + dirIndex_;
FAIL:
  return 0;
}
//------------------------------------------------------------------------------
/** Close a file and force cached data and directory information
 *  to be written to the storage device.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include no file is open or an I/O error.
 */
bool SdBaseFile::close() {
  bool rtn = sync();
  type_ = FAT_FILE_TYPE_CLOSED;
  return rtn;
}
//------------------------------------------------------------------------------
/** Check for contiguous file and return its raw block range.
 *
 * \param[out] bgnBlock the first block address for the file.
 * \param[out] endBlock the last  block address for the file.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include file is not contiguous, file has zero length
 * or an I/O error occurred.
 */
bool SdBaseFile::contiguousRange(uint32_t* bgnBlock, uint32_t* endBlock) {
  // error if no blocks
  if (firstCluster_ == 0) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  for (uint32_t c = firstCluster_; ; c++) {
    uint32_t next;
    if (!vol_->fatGet(c, &next)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // check for contiguous
    if (next != (c + 1)) {
      // error if not end of chain
      if (!vol_->isEOC(next)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      *bgnBlock = vol_->clusterStartBlock(firstCluster_);
      *endBlock = vol_->clusterStartBlock(c)
                  + vol_->blocksPerCluster_ - 1;
      return true;
    }
  }

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Create and open a new contiguous file of a specified size.
 *
 * \note This function only supports short DOS 8.3 names.
 * See open() for more information.
 *
 * \param[in] dirFile The directory where the file will be created.
 * \param[in] path A path with a valid DOS 8.3 file name.
 * \param[in] size The desired file size.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include \a path contains
 * an invalid DOS 8.3 file name, the FAT volume has not been initialized,
 * a file is already open, the file already exists, the root
 * directory is full or an I/O error.
 *
 */
bool SdBaseFile::createContiguous(SdBaseFile* dirFile,
                                  PGM_P path, uint32_t size) {
  uint32_t count;
  // don't allow zero length file
  if (size == 0) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (!open(dirFile, path, O_CREAT | O_EXCL | O_RDWR)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // calculate number of clusters needed
  count = ((size - 1) >> (vol_->clusterSizeShift_ + 9)) + 1;

  // allocate clusters
  if (!vol_->allocContiguous(count, &firstCluster_)) {
    remove();
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  fileSize_ = size;

  // insure sync() will update dir entry
  flags_ |= F_FILE_DIR_DIRTY;

  return sync();

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Return a file's directory entry.
 *
 * \param[out] dir Location for return of the file's directory entry.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::dirEntry(dir_t* dir) {
  dir_t* p;
  // make sure fields on SD are correct
  if (!sync()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // read entry
  p = cacheDirEntry(SdVolume::CACHE_FOR_READ);
  if (!p) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // copy to caller's struct
  memcpy(dir, p, sizeof(dir_t));
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Format the name field of \a dir into the 13 byte array
 * \a name in standard 8.3 short name format.
 *
 * \param[in] dir The directory structure containing the name.
 * \param[out] name A 13 byte char array for the formatted name.
 */
void SdBaseFile::dirName(const dir_t& dir, char* name) {
  uint8_t j = 0;
  for (uint8_t i = 0; i < 11; i++) {
    if (dir.name[i] == ' ') continue;
    if (i == 8) name[j++] = '.';
    name[j++] = dir.name[i];
  }
  name[j] = 0;
}
//------------------------------------------------------------------------------
/** Test for the existence of a file in a directory
 *
 * \param[in] name Name of the file to be tested for.
 *
 * The calling instance must be an open directory file.
 *
 * dirFile.exists("TOFIND.TXT") searches for "TOFIND.TXT" in  the directory
 * dirFile.
 *
 * \return true if the file exists else false.
 */
bool SdBaseFile::exists(PGM_P name) {
  SdBaseFile file;
  return file.open(this, name, O_READ);
}
//------------------------------------------------------------------------------
/**
 * Get a string from a file.
 *
 * fgets() reads bytes from a file into the array pointed to by \a str, until
 * \a num - 1 bytes are read, or a delimiter is read and transferred to \a str,
 * or end-of-file is encountered. The string is then terminated
 * with a null byte.
 *
 * fgets() deletes CR, '\\r', from the string.  This insures only a '\\n'
 * terminates the string for Windows text files which use CRLF for newline.
 *
 * \param[out] str Pointer to the array where the string is stored.
 * \param[in] num Maximum number of characters to be read
 * (including the final null byte). Usually the length
 * of the array \a str is used.
 * \param[in] delim Optional set of delimiters. The default is "\n".
 *
 * \return For success fgets() returns the length of the string in \a str.
 * If no data is read, fgets() returns zero for EOF or -1 if an error occurred.
 **/
int16_t SdBaseFile::fgets(char* str, int16_t num, char* delim) {
  char ch;
  int16_t n = 0;
  int16_t r = -1;
  while ((n + 1) < num && (r = read(&ch, 1)) == 1) {
    // delete CR
    if (ch == '\r') continue;
    str[n++] = ch;
    if (!delim) {
      if (ch == '\n') break;
    }
    else {
      if (strchr(delim, ch)) break;
    }
  }
  if (r < 0) {
    // read error
    return -1;
  }
  str[n] = '\0';
  return n;
}
//------------------------------------------------------------------------------
/** Get a file's name
 *
 * \param[out] name An array of 13 characters for the file's name.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::getFilename(char* name) {
  if (!isOpen()) {
    DBG_FAIL_MACRO;
    return false;
  }
  if (isRoot()) {
    name[0] = '/';
    name[1] = '\0';
    return true;
  }
  // cache entry
  dir_t* p = cacheDirEntry(SdVolume::CACHE_FOR_READ);
  if (!p) {
    DBG_FAIL_MACRO;
    return false;
  }

  // format name
  dirName(*p, name);
  return true;
}

//------------------------------------------------------------------------------
void SdBaseFile::getpos(FatPos_t* pos) {
  pos->position = curPosition_;
  pos->cluster = curCluster_;
}

uint8_t SdBaseFile::lsRecursive(SdBaseFile* parent, uint8_t level, char* findFilename, SdBaseFile* pParentFound, bool isJson) {
  dir_t *p = NULL;
  //uint8_t cnt=0;
  //char *oldpathend = pathend;
  #if ENABLED(JSON_OUTPUT)
    bool firstFile = true;
  #endif

  parent->rewind();

  while ((p = parent->getLongFilename(p, card.tempLongFilename))) {
    //HAL::pingWatchdog();
    if (! (DIR_IS_FILE(p) || DIR_IS_SUBDIR(p))) continue;
    if (strcmp(card.tempLongFilename, "..") == 0) continue;
    if (card.tempLongFilename[0] == '.') continue; // MAC CRAP
    if (DIR_IS_SUBDIR(p)) {
      if (level >= SD_MAX_FOLDER_DEPTH) continue; // can't go deeper
      if (level < SD_MAX_FOLDER_DEPTH && findFilename == NULL) {
        if (level && !isJson) {
          SERIAL_TXT(card.fileName);
          SERIAL_CHR('/');
        }
        #if ENABLED(JSON_OUTPUT)
          if (isJson) {
            if (!firstFile) SERIAL_CHR(',');
            SERIAL_CHR('"'); SERIAL_CHR('*');
            CardReader::printEscapeChars(card.tempLongFilename);
            SERIAL_CHR('"');
            firstFile = false;
          }
          else {
            SERIAL_TXT(card.tempLongFilename);
            SERIAL_CHR('/'); SERIAL_EOL(); // End with / to mark it as directory entry, so we can see empty directories.
          }
        #else
          SERIAL_TXT(card.tempLongFilename);
          SERIAL_CHR('/'); SERIAL_EOL();// End with / to mark it as directory entry, so we can see empty directories.
        #endif
      }
      SdBaseFile next;
      char *tmp;

      if(level) strcat(card.fileName, "/");

      strcat(card.fileName, card.tempLongFilename);
      uint16_t index = (parent->curPosition()-31) >> 5;

      if(!isJson && next.open(parent, index, O_READ)) {
        if (next.lsRecursive(&next, level + 1, findFilename, pParentFound, false))
          return true;
      }
      parent->seekSet(32 * (index + 1));
      if ((tmp = strrchr(card.fileName, '/')) != NULL)
        *tmp = 0;
      else
        *card.fileName = 0;
    }
    else {
      if (findFilename != NULL) {
        int8_t cFullname;
        cFullname = strlen(card.fileName);
        if (RFstrnicmp(card.fileName, findFilename, cFullname) == 0) {
          if (cFullname > 0)
            cFullname++;
          if (RFstricmp(card.tempLongFilename, findFilename + cFullname) == 0) {
            if (pParentFound != NULL)
              *pParentFound = *parent;
            return true;
          }
        }
      }
      else {
        if(level && !isJson) {
          SERIAL_TXT(card.fileName);
          SERIAL_CHR('/');
        }
        #if ENABLED(JSON_OUTPUT)
          if (isJson) {
            if (!firstFile) SERIAL_CHR(',');
            SERIAL_CHR('"');
            CardReader::printEscapeChars(card.tempLongFilename);
            SERIAL_CHR('"');
            firstFile = false;
          }
          else
        #endif
        {
          SERIAL_TXT(card.tempLongFilename);
          #if ENABLED(SD_EXTENDED_DIR)
            SERIAL_MV(" ", (long) p->fileSize);
          #endif
          SERIAL_EOL();
        }
      }
    }
  }
  return false;
}

//------------------------------------------------------------------------------
/** List directory contents.
 * list to indicate subdirectory level.
 */
void SdBaseFile::ls() {
  SdBaseFile parent;
  rewind();
  *card.fileName = 0;
  pathend = card.fileName;
  parent = *this;
  lsRecursive(&parent, 0, NULL, NULL, false);
}

#if ENABLED(JSON_OUTPUT)
void SdBaseFile::lsJSON() {
  SdBaseFile parent;
  rewind();
  *card.fileName = 0;
  parent = *this;
  lsRecursive(&parent, 0, NULL, NULL, true);
}
#endif

//------------------------------------------------------------------------------
// saves 32 bytes on stack for ls recursion
// return 0 - EOF, 1 - normal file, or 2 - directory
int8_t SdBaseFile::lsPrintNext(uint8_t flags, uint8_t indent) {
  dir_t dir;
  //uint8_t w = 0;
  while (1) {
    if (read(&dir, sizeof(dir)) != sizeof(dir)) return 0;
    if (dir.name[0] == DIR_NAME_FREE) return 0;

    // skip deleted entry and entries for . and  ..
    if (dir.name[0] != DIR_NAME_DELETED && dir.name[0] != '.'
      && DIR_IS_FILE_OR_SUBDIR(&dir)) break;
  }
  // indent for dir level
  for (uint8_t i = 0; i < indent; i++) SERIAL_CHR(' ');

  printDirName(dir, flags & (LS_DATE | LS_SIZE) ? 14 : 0, true);

  // print modify date/time if requested
  if (flags & LS_DATE) {
    SERIAL_CHR(' ');
    printFatDate(dir.lastWriteDate);
    SERIAL_CHR(' ');
    printFatTime(dir.lastWriteTime);
  }
  // print size if requested
  if (!DIR_IS_SUBDIR(&dir) && (flags & LS_SIZE)) {
    SERIAL_CHR(' ');
    SERIAL_VAL(dir.fileSize);
  }
  SERIAL_EOL();
  return DIR_IS_FILE(&dir) ? 1 : 2;
}
//------------------------------------------------------------------------------
// format directory name field from a 8.3 name string

bool SdBaseFile::make83Name(PGM_P str, uint8_t* name, const char** ptr) {
  uint8_t c;
  uint8_t n = 7;  // max index for part before dot
  uint8_t i = 0;
  // blank fill name and extension
  while (i < 11) name[i++] = ' ';
  i = 0;
  while (*str != '\0' && *str != '/') {
    c = *str++;
    if (c == '.') {
      if (n == 10) {
        DBG_FAIL_MACRO;
        goto FAIL;  // only one dot allowed
      }
      n = 10;  // max index for full 8.3 name
      i = 8;   // place for extension
    }
    else {
      // illegal FAT characters
      #if ENABLED(__AVR__)
        // store chars in flash
        PGM_P p = PSTR("|<>^+=?/[];,*\"\\");
        uint8_t b;
        while ((b = pgm_read_byte(p++))) {
          if (b == c) {
            DBG_FAIL_MACRO;
            goto FAIL;
          }
        }
      #else  // __AVR__
        // store chars in RAM
        if (strchr("|<>^+=?/[];,*\"\\", c)) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
      #endif  // __AVR__
      // check size and only allow ASCII printable characters
      if (i > n || c < 0x20 || c > 0x7E) {
        c = '_';
      }
      // only upper case allowed in 8.3 names - convert lower to upper
      name[i++] = c < 'a' || c > 'z' ?  c : c + ('A' - 'a');
    }
  }
  *ptr = str;
  // must have a file name, extension is optional
  return name[0] != ' ';

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Make a new directory.
 *
 * \param[in] parent An open SdFat instance for the directory that will contain
 * the new directory.
 *
 * \param[in] path A path with a valid 8.3 DOS name for the new directory.
 *
 * \param[in] pFlag Create missing parent directories if true.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include this file is already open, \a parent is not a
 * directory, \a path is invalid or already exists in \a parent.
 */
bool SdBaseFile::mkdir(SdBaseFile* parent, PGM_P path, bool pFlag) {

  uint8_t dname[LONG_FILENAME_LENGTH+1];
  SdBaseFile newParent;

  if (openParentReturnFile(parent, path, dname, &newParent, pFlag)) {
    return mkdir(&newParent, dname);
  }
  return false;
}
//------------------------------------------------------------------------------
bool SdBaseFile::mkdir(SdBaseFile* parent, const uint8_t *dname) {
  dir_t d;

  if (!parent->isDir()) {
    DBG_FAIL_MACRO;
    return false;
  }

  // create a normal file
  if (!open(parent, dname, O_CREAT | O_EXCL | O_RDWR, true)) {
    DBG_FAIL_MACRO;
    return false;
  }

  // make entry for '.'
  memset(&d, 0, sizeof(d));
  d.creationDate = FAT_DEFAULT_DATE;
  d.creationTime = FAT_DEFAULT_TIME;
  d.lastAccessDate = d.creationDate;
  d.lastWriteDate = d.creationDate;
  d.lastWriteTime = d.creationTime;

  d.name[0] = '.';
  d.attributes = DIR_ATT_DIRECTORY;
  for (uint8_t i = 1; i < 11; i++) d.name[i] = ' ';

  if (write(&d, sizeof(dir_t)) < 0)
    return false;
  sync();

  // make entry for '..'
  d.name[1] = '.';
  if (parent->isRoot()) {
    d.firstClusterLow = 0;
    d.firstClusterHigh = 0;
  }
  else {
    d.firstClusterLow = parent->firstCluster_ & 0xFFFF;
    d.firstClusterHigh = parent->firstCluster_ >> 16;
  }
  if (write(&d, sizeof(dir_t)) < 0)
    return false;
  sync();
  memset(&d, 0, sizeof(dir_t));
  if (write(&d, sizeof(dir_t)) < 0)
    return false;
  sync();
//  fileSize_ = 0;
  type_ = FAT_FILE_TYPE_SUBDIR;
  flags_ |= F_FILE_DIR_DIRTY;
  return true;
}
//------------------------------------------------------------------------------
/** Open a file in the current working directory.
 *
 * \param[in] path A path with a valid 8.3 DOS name for a file to be opened.
 *
 * \param[in] oflag Values for \a oflag are constructed by a bitwise-inclusive
 * OR of open flags. see SdBaseFile::open(SdBaseFile*, const char*, uint8_t).
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::open(PGM_P path, uint8_t oflag) {
  return open(cwd_, path, oflag);
}
//------------------------------------------------------------------------------
/** Open a file or directory by name.
 *
 * \param[in] dirFile An open SdFat instance for the directory containing the
 * file to be opened.
 *
 * \param[in] path A path with a valid 8.3 DOS name for a file to be opened.
 *
 * \param[in] oflag Values for \a oflag are constructed by a bitwise-inclusive
 * OR of flags from the following list
 *
 * O_READ - Open for reading.
 *
 * O_RDONLY - Same as O_READ.
 *
 * O_WRITE - Open for writing.
 *
 * O_WRONLY - Same as O_WRITE.
 *
 * O_RDWR - Open for reading and writing.
 *
 * O_APPEND - If set, the file offset shall be set to the end of the
 * file prior to each write.
 *
 * O_AT_END - Set the initial position at the end of the file.
 *
 * O_CREAT - If the file exists, this flag has no effect except as noted
 * under O_EXCL below. Otherwise, the file shall be created
 *
 * O_EXCL - If O_CREAT and O_EXCL are set, open() shall fail if the file exists.
 *
 * O_SYNC - Call sync() after each write.  This flag should not be used with
 * write(uint8_t), write_P(PGM_P), writelnmkdir_P(PGM_P), or the Arduino Print class.
 * These functions do character at a time writes so sync() will be called
 * after each byte.
 *
 * O_TRUNC - If the file exists and is a regular file, and the file is
 * successfully opened and is not read only, its length shall be truncated to 0.
 *
 * WARNING: A given file must not be opened by more than one SdBaseFile object
 * of file corruption may occur.
 *
 * \note Directory files must be opened read only.  Write and truncation is
 * not allowed for directory files.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include this file is already open, \a dirFile is not
 * a directory, \a path is invalid, the file does not exist
 * or can't be opened in the access mode specified by oflag.
 */

 bool SdBaseFile::openParentReturnFile(SdBaseFile* dirFile, PGM_P path, uint8_t *dname, SdBaseFile *newParent, bool bMakeDirs) {
  SdBaseFile dir1, dir2;
  SdBaseFile *parent = dirFile;
  //dir_t *pEntry;
  SdBaseFile *sub = &dir1;
  char *p;
  //bool bFound;

  *dname = 0;

  if (!dirFile) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }

  // error if already open
  if (isOpen()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }

  if (*path == '/') {
    while (*path == '/') path++;
    if (!dirFile->isRoot()) {
      if (!dir2.openRoot(dirFile->vol_)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      parent = &dir2;
    }
  }

  // Traverse the Long Directory Name Path until we get to the LEAF (long file name)
  while ((p = strchr(path, '/')) != NULL) {
    int8_t cb = p-path;

    memcpy(dname, path, cb);
    *(dname+cb) = 0;

    if (*(p+1) == 0) goto success;
    //bFound = false;
    if (!sub->open(parent, dname, O_READ, false)) {
      if (!bMakeDirs)
         return false;
      if (!sub->mkdir(parent, dname)) {
        return false;
      }
    }

    if (parent != dirFile) parent->close();
    parent = sub;
    sub = parent != &dir1 ? &dir1 : &dir2;
    path = p+1;
  }

  strcpy((char *)dname, path);

success:
  *newParent = *parent;
  return true;

FAIL:
  return false;
}

bool SdBaseFile::open(SdBaseFile* dirFile, PGM_P path, uint8_t oflag) {
  uint8_t dname[LONG_FILENAME_LENGTH + 1];
  SdBaseFile parent;

  if (openParentReturnFile(dirFile, path, dname, &parent, false)) {
    if (*dname == 0) return true;
    return open(&parent, dname, oflag, false);
  }

  return false;
}


uint8_t SdBaseFile::lfn_checksum(const unsigned char *pFCBName) {
  int i;
  unsigned char sum = 0;

  for (i = 11; i; i--)
    sum = ((sum & 1) << 7) + (sum >> 1) + *pFCBName++;

  return sum;
}
//------------------------------------------------------------------------------
// open with filename in dname
bool SdBaseFile::open(SdBaseFile* dirFile, const uint8_t *dname, uint8_t oflag, bool bDir) {
  bool emptyFound = false;
  uint8_t index = 0;
  dir_t tempDir, *p = NULL;
  PGM_P tempPtr;
  char newName[SHORT_FILENAME_LENGTH + 2];
  bool bShortName = false;
  int8_t cVFATNeeded = -1, cVFATFoundCur;
  uint32_t wIndexPos = 0;
  uint8_t cbFilename;
  char *Filename = (char *)dname;

  vol_ = dirFile->vol_;
  dirFile->rewind();
  // search for file

  if (oflag & O_CREAT) {
    int8_t cb = strlen((char *)dname);
    bShortName = cb < 9;
    cVFATNeeded = (cb / 13) + (cb % 13 == 0 ? 0 : 1);
  }

  while ((p = dirFile->getLongFilename(p, card.tempLongFilename))) {
    //HAL::pingWatchdog();
    index = (0xF & ((dirFile->curPosition_ - 31) >> 5));
    if (RFstricmp(card.tempLongFilename, (char *)dname) == 0) {
      if (oflag & O_EXCL) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      return openCachedEntry(index, oflag);
    }
  }

  // don't create unless O_CREAT and O_WRITE
  if (!(oflag & O_CREAT) || !(oflag & O_WRITE)) {
    goto FAIL;
  }

  dirFile->findSpace(&tempDir, cVFATNeeded, &cVFATFoundCur, &wIndexPos);
  if (wIndexPos != 0) {
    emptyFound = true;
    index = wIndexPos >> 5;
  }
  else {
    // only 512 entries allowed in FAT16 Root Fixed dir
    if (dirFile->type() == FAT_FILE_TYPE_ROOT_FIXED && (dirFile->curPosition_ >> 5) >= 512)
      goto FAIL;
    cVFATFoundCur = cVFATNeeded + 1;
    if (dirFile->curPosition_ > 0)
      wIndexPos = dirFile->curPosition_-32;
  }
  p = &tempDir;

  dirFile->flags_ |= O_WRITE;
  dirFile->seekSet(wIndexPos);

  // Create LONG FILE NAMES and LONG DIRECTORIES HERE
  // FILL IN MULTIPLE dir_t enteries..
  // DO a test and and make all files created have a long file name of "XXXXXXX <shortname>"
  if (!bShortName) {
    char *pExt, szExt[5];

    // Generate 8.3 from longfile name
    if ((pExt = strchr((char *)dname, '.')) != NULL) {
      strncpy(szExt, pExt, 4);
      szExt[4] = 0;
      if (pExt > (char*)dname + 6)
        pExt = (char*)dname + 6;
    }
    else {
      szExt[0] = 0;
      pExt = (char*)dname+6;
    }
    uint8_t cb = pExt-(char *)dname;
    memcpy(newName, dname, cb);
    newName[cb] = 0;
    strcat(newName, "~1");
    strcat(newName, szExt);
  }
  else {
    strcpy(newName, (char *)dname);
  }

  uint8_t checksum;

  make83Name(newName, (uint8_t *)p->name, &tempPtr);
  checksum = lfn_checksum((unsigned char *)p->name);
  cbFilename = strlen(Filename);

  // Write Long File Name VFAT entries to file
  for (uint8_t iBlk = cVFATNeeded; iBlk > 0; iBlk--) {
    vfat_t *VFAT = (vfat_t *)p;
    uint8_t n;

    n = (iBlk - 1) * 13;
    memset(p, 0, sizeof(*p));
    p->attributes = DIR_ATT_LONG_NAME;
    VFAT->sequenceNumber = iBlk | (iBlk == cVFATNeeded ? 0x40 : 0);

    uint16_t *pName = VFAT->name1;

    for(int8_t i = 0; i < 13; i++) {
      if (n+i > cbFilename)
        *pName++ = 0xFFFF;
      else
        *pName++ = (uint16_t)Filename[n + i];
      if (i == 4)
        pName = VFAT->name2;
      else if (i == 10)
        pName = VFAT->name3;
    }
    VFAT->checksum = checksum;
    if (dirFile->write(p, sizeof(dir_t)) < 0)
      goto FAIL;
    dirFile->sync();
  }
  // END WRITING LONG FILE NAME BLK

  // Start 8.3 file init
  // initialize as empty file
  memset(p, 0, sizeof(*p));

  make83Name(newName, (uint8_t *)p->name, &tempPtr);

  p->attributes = bDir ? DIR_ATT_DIRECTORY : DIR_ATT_ARCHIVE;

  p->creationDate = FAT_DEFAULT_DATE;
  p->creationTime = FAT_DEFAULT_TIME;
  p->lastAccessDate = p->creationDate;
  p->lastWriteDate = p->creationDate;
  p->lastWriteTime = p->creationTime;

  if (dirFile->write(p, sizeof(dir_t)) < 0)
    goto FAIL;
  dirFile->sync();

  memset(p, 0, sizeof(*p));

  if (emptyFound)
    p->name[0] = DIR_NAME_DELETED;

  for(int8_t i = 0; i < cVFATFoundCur - cVFATNeeded; i++) {
    if (dirFile->write(p, sizeof(dir_t)) < 0)
      goto FAIL;
    dirFile->sync();
  }

  return open(dirFile, (wIndexPos >> 5) + (cVFATNeeded), oflag & ~O_EXCL);

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Open a file by index.
 *
 * \param[in] dirFile An open SdFat instance for the directory.
 *
 * \param[in] index The \a index of the directory entry for the file to be
 * opened.  The value for \a index is (directory file position)/32.
 *
 * \param[in] oflag Values for \a oflag are constructed by a bitwise-inclusive
 * OR of flags O_READ, O_WRITE, O_TRUNC, and O_SYNC.
 *
 * See open() by path for definition of flags.
 * \return true for success or false for failure.
 */
bool SdBaseFile::open(SdBaseFile* dirFile, uint16_t index, uint8_t oflag) {
  dir_t* p;

  vol_ = dirFile->vol_;

  // error if already open
  if (isOpen() || !dirFile) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }

  // don't open existing file if O_EXCL - user call error
  if (oflag & O_EXCL) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // seek to location of entry
  if (!dirFile->seekSet(32 * index)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // read entry into cache
  p = dirFile->readDirCache();
  if (!p) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // error if empty slot or '.' or '..'
  if (p->name[0] == DIR_NAME_FREE ||
      p->name[0] == DIR_NAME_DELETED || p->name[0] == '.') {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // open cached entry
  return openCachedEntry(index & 0xF, oflag);

FAIL:
  return false;
}
//------------------------------------------------------------------------------
// open a cached directory entry. Assumes vol_ is initialized
bool SdBaseFile::openCachedEntry(uint8_t dirIndex, uint8_t oflag) {
  // location of entry in cache
  dir_t* p = &vol_->cacheAddress()->dir[dirIndex];

  // write or truncate is an error for a directory or read-only file
  if (p->attributes & (DIR_ATT_READ_ONLY | DIR_ATT_DIRECTORY)) {
//    if (oflag & (O_WRITE | O_TRUNC)) {
//      DBG_FAIL_MACRO;
//      goto FAIL;
//    }
  }
  // remember location of directory entry on SD
  dirBlock_ = vol_->cacheBlockNumber();
  dirIndex_ = dirIndex;

  // copy first cluster number for directory fields
  firstCluster_ = (uint32_t)p->firstClusterHigh << 16;
  firstCluster_ |= p->firstClusterLow;

  // make sure it is a normal file or subdirectory
  if (DIR_IS_FILE(p)) {
    fileSize_ = p->fileSize;
    type_ = FAT_FILE_TYPE_NORMAL;
  }
  else if (DIR_IS_SUBDIR(p)) {
    if (!setDirSize()) {
      fileSize_= 0;
    }
    type_ = FAT_FILE_TYPE_SUBDIR;
  }
  else {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // save open flags for read/write
  flags_ = oflag & F_OFLAG;

  // set to start of file
  curCluster_ = 0;
  curPosition_ = 0;
  if ((oflag & O_TRUNC) && !truncate(0)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  return oflag & O_AT_END ? seekEnd(0) : true;

FAIL:
  type_ = FAT_FILE_TYPE_CLOSED;
  return false;
}
//------------------------------------------------------------------------------
/** Open the next file or subdirectory in a directory.
 *
 * \param[in] dirFile An open SdFat instance for the directory containing the
 * file to be opened.
 *
 * \param[in] oflag Values for \a oflag are constructed by a bitwise-inclusive
 * OR of flags O_READ, O_WRITE, O_TRUNC, and O_SYNC.
 *
 * See open() by path for definition of flags.
 * \return true for success or false for failure.
 */
bool SdBaseFile::openNext(SdBaseFile* dirFile, uint8_t oflag) {
  dir_t* p;
  uint8_t index;

  if (!dirFile) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // error if already open
  if (isOpen()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  vol_ = dirFile->vol_;

  while (1) {
    index = 0xF & (dirFile->curPosition_ >> 5);

    // read entry into cache
    p = dirFile->readDirCache();
    if (!p) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // done if last entry
    if (p->name[0] == DIR_NAME_FREE) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // skip empty slot or '.' or '..'
    if (p->name[0] == DIR_NAME_DELETED || p->name[0] == '.') {
      continue;
    }
    // must be file or dir
    if (DIR_IS_FILE_OR_SUBDIR(p)) {
      return openCachedEntry(index, oflag);
    }
  }

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Open a directory's parent directory.
 *
 * \param[in] dir Parent of this directory will be opened.  Must not be root.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::openParent(SdBaseFile* dir) {
  dir_t entry;
  dir_t* p;
  SdBaseFile file;
  uint32_t c;
  uint32_t cluster;
  uint32_t lbn;
  cache_t* pc;
  // error if already open or dir is root or dir is not a directory
  if (isOpen() || !dir || dir->isRoot() || !dir->isDir()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  vol_ = dir->vol_;
  // position to '..'
  if (!dir->seekSet(32)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // read '..' entry
  if (dir->read(&entry, sizeof(entry)) != 32) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // verify it is '..'
  if (entry.name[0] != '.' || entry.name[1] != '.') {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // start cluster for '..'
  cluster = entry.firstClusterLow;
  cluster |= (uint32_t)entry.firstClusterHigh << 16;
  if (cluster == 0) return openRoot(vol_);
  // start block for '..'
  lbn = vol_->clusterStartBlock(cluster);
  // first block of parent dir
    pc = vol_->cacheFetch(lbn, SdVolume::CACHE_FOR_READ);
    if (!pc) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  p = &pc->dir[1];
  // verify name for '../..'
  if (p->name[0] != '.' || p->name[1] != '.') {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // '..' is pointer to first cluster of parent. open '../..' to find parent
  if (p->firstClusterHigh == 0 && p->firstClusterLow == 0) {
    if (!file.openRoot(dir->volume())) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  } else {
    if (!file.openCachedEntry(1, O_READ)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  // search for parent in '../..'
  do {
    if (file.readDir(&entry) != 32) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    c = entry.firstClusterLow;
    c |= (uint32_t)entry.firstClusterHigh << 16;
  } while (c != cluster);
  // open parent
  return open(&file, file.curPosition() / 32 - 1, O_READ);

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Open a volume's root directory.
 *
 * \param[in] vol The FAT volume containing the root directory to be opened.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include the file is already open, the FAT volume has
 * not been initialized or it a FAT12 volume.
 */
bool SdBaseFile::openRoot(SdVolume* vol) {
  // error if file is already open
  if (isOpen()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  vol_ = vol;
  if (vol->fatType() == 16 || (FAT12_SUPPORT && vol->fatType() == 12)) {
    type_ = FAT_FILE_TYPE_ROOT_FIXED;
    firstCluster_ = 0;
    fileSize_ = 32 * vol->rootDirEntryCount();
  }
  else if (vol->fatType() == 32) {
    type_ = FAT_FILE_TYPE_ROOT32;
    firstCluster_ = vol->rootDirStart();
    if (!setDirSize()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  else {
    // volume is not initialized, invalid, or FAT12 without support
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // read only
  flags_ = O_READ;

  // set to start of file
  curCluster_ = 0;
  curPosition_ = 0;

  // root has no directory entry
  dirBlock_ = 0;
  dirIndex_ = 0;
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Return the next available byte without consuming it.
 *
 * \return The byte if no error and not at eof else -1;
 */
int SdBaseFile::peek() {
  FatPos_t pos;
  getpos(&pos);
  int c = read();
  if (c >= 0) setpos(&pos);
  return c;
}
//------------------------------------------------------------------------------
/** %Print the name field of a directory entry in 8.3 format.
 * \param[in] pr Print stream for output.
 * \param[in] dir The directory structure containing the name.
 * \param[in] width Blank fill name if length is less than \a width.
 * \param[in] printSlash Print '/' after directory names if true.
 */
void SdBaseFile::printDirName(const dir_t& dir, uint8_t width, bool printSlash) {
  uint8_t w = 0;
  for (uint8_t i = 0; i < 11; i++) {
    if (dir.name[i] == ' ')continue;
    if (i == 8) {
      SERIAL_CHR('.');
      w++;
    }
    SERIAL_CHR((char)dir.name[i]);
    w++;
  }
  if (DIR_IS_SUBDIR(&dir) && printSlash) {
    SERIAL_CHR('/');
    w++;
  }
  while (w < width) {
    SERIAL_CHR(' ');
    w++;
  }
}
//------------------------------------------------------------------------------
// print uint8_t with width 2
static void print2u(uint8_t v) {
  if (v < 10) SERIAL_CHR('0');
  SERIAL_VAL((int)v);
}
//------------------------------------------------------------------------------
/** Print a file's creation date and time
 *
 * \param[in] pr Print stream for output.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::printCreateDateTime() {
  dir_t dir;
  if (!dirEntry(&dir)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  printFatDate(dir.creationDate);
  SERIAL_CHR(' ');
  printFatTime(dir.creationTime);
  return true;

FAIL:
  return false;
}

//------------------------------------------------------------------------------
/** %Print a directory date field.
 *
 *  Format is yyyy-mm-dd.
 *
 * \param[in] pr Print stream for output.
 * \param[in] fatDate The date field from a directory entry.
 */
void SdBaseFile::printFatDate(uint16_t fatDate) {
  SERIAL_VAL((int)FAT_YEAR(fatDate));
  SERIAL_CHR('-');
  print2u(FAT_MONTH(fatDate));
  SERIAL_CHR('-');
  print2u(FAT_DAY(fatDate));
}

//------------------------------------------------------------------------------
/** %Print a directory time field.
 *
 * Format is hh:mm:ss.
 *
 * \param[in] pr Print stream for output.
 * \param[in] fatTime The time field from a directory entry.
 */
void SdBaseFile::printFatTime(uint16_t fatTime) {
  print2u(FAT_HOUR(fatTime));
  SERIAL_CHR(':');
  print2u(FAT_MINUTE(fatTime));
  SERIAL_CHR(':');
  print2u(FAT_SECOND(fatTime));
}
//------------------------------------------------------------------------------
/** Print a file's modify date and time
 *
 * \param[in] pr Print stream for output.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::printModifyDateTime() {
  dir_t dir;
  if (!dirEntry(&dir)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  printFatDate(dir.lastWriteDate);
  SERIAL_CHR(' ');
  printFatTime(dir.lastWriteTime);
  return true;

FAIL:
  return false;
}
/** Template for SdBaseFile::printField() */

template <typename Type>

static int printFieldT(SdBaseFile* file, char sign, Type value, char term) {
  char buf[3*sizeof(Type) + 3];
  char* str = &buf[sizeof(buf)];

  if (term) {
    *--str = term;
    if (term == '\n') {
      *--str = '\r';
    }
  }
  do {
    Type m = value;
    value /= 10;
    *--str = '0' + m - 10*value;
  } while (value);
  if (sign) {
    *--str = sign;
  }
  return file->write(str, &buf[sizeof(buf)] - str);
}
//------------------------------------------------------------------------------
/** Print a number followed by a field terminator.
 * \param[in] value The number to be printed.
 * \param[in] term The field terminator.  Use '\\n' for CR LF.
 * \return The number of bytes written or -1 if an error occurs.
 */
int SdBaseFile::printField(uint16_t value, char term) {
  return printFieldT(this, 0, value, term);
}
//------------------------------------------------------------------------------
/** Print a number followed by a field terminator.
 * \param[in] value The number to be printed.
 * \param[in] term The field terminator.  Use '\\n' for CR LF.
 * \return The number of bytes written or -1 if an error occurs.
 */
int SdBaseFile::printField(int16_t value, char term) {
  char sign = 0;
  if (value < 0) {
    sign = '-';
    value = -value;
  }
  return printFieldT(this, sign, (uint16_t)value, term);
}
//------------------------------------------------------------------------------
/** Print a number followed by a field terminator.
 * \param[in] value The number to be printed.
 * \param[in] term The field terminator.  Use '\\n' for CR LF.
 * \return The number of bytes written or -1 if an error occurs.
 */
int SdBaseFile::printField(uint32_t value, char term) {
  return printFieldT(this, 0, value, term);
}
//------------------------------------------------------------------------------
/** Print a number followed by a field terminator.
 * \param[in] value The number to be printed.
 * \param[in] term The field terminator.  Use '\\n' for CR LF.
 * \return The number of bytes written or -1 if an error occurs.
 */
int SdBaseFile::printField(int32_t value, char term) {
  char sign = 0;
  if (value < 0) {
    sign = '-';
    value = -value;
  }
  return printFieldT(this, sign, (uint32_t)value, term);
}

//-----------------------------------------------------------------------------
//------------------------------------------------------------------------------
/** Print a file's name
 *
 * \param[in] pr Print stream for output.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::printName() {
  char name[13];
  if (!getFilename(name)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  SERIAL_TXT(name);
  return true;
FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Read the next byte from a file.
 *
 * \return For success read returns the next byte in the file as an int.
 * If an error occurs or end of file is reached -1 is returned.
 */
int16_t SdBaseFile::read() {
  uint8_t b;
  return read(&b, 1) == 1 ? b : -1;
}
//------------------------------------------------------------------------------
/** Read data from a file starting at the current position.
 *
 * \param[out] buf Pointer to the location that will receive the data.
 *
 * \param[in] nbyte Maximum number of bytes to read.
 *
 * \return For success read() returns the number of bytes read.
 * A value less than \a nbyte, including zero, will be returned
 * if end of file is reached.
 * If an error occurs, read() returns -1.  Possible errors include
 * read() called before a file has been opened, corrupt file system
 * or an I/O error occurred.
 */
int SdBaseFile::read(void* buf, size_t nbyte) {
  uint8_t blockOfCluster;
  uint8_t* dst = reinterpret_cast<uint8_t*>(buf);
  uint16_t offset;
  size_t toRead;
  uint32_t block;  // raw device block number
  cache_t* pc;

  // error if not open or write only
  if (!isOpen() || !(flags_ & O_READ)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // max bytes left in file
  if (nbyte >= (fileSize_ - curPosition_)) {
    nbyte = fileSize_ - curPosition_;
  }
  // amount left to read
  toRead = nbyte;
  while (toRead > 0) {
    size_t n;
    offset = curPosition_ & 0x1FF;  // offset in block
    blockOfCluster = vol_->blockOfCluster(curPosition_);
    if (type_ == FAT_FILE_TYPE_ROOT_FIXED) {
      block = vol_->rootDirStart() + (curPosition_ >> 9);
    }
    else {
      if (offset == 0 && blockOfCluster == 0) {
        // start of new cluster
        if (curPosition_ == 0) {
          // use first cluster in file
          curCluster_ = firstCluster_;
        }
        else {
          // get next cluster from FAT
          if (!vol_->fatGet(curCluster_, &curCluster_)) {
            DBG_FAIL_MACRO;
            goto FAIL;
          }
        }
      }
      block = vol_->clusterStartBlock(curCluster_) + blockOfCluster;
    }
    if (offset != 0 || toRead < 512 || block == vol_->cacheBlockNumber()) {
      // amount to be read from current block
      n = 512 - offset;
      if (n > toRead) n = toRead;
      // read block to cache and copy data to caller
      pc = vol_->cacheFetch(block, SdVolume::CACHE_FOR_READ);
      if (!pc) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      uint8_t* src = pc->data + offset;
      memcpy(dst, src, n);
    }
    else if (!USE_MULTI_BLOCK_SD_IO || toRead < 1024) {
      // read single block
      n = 512;
      if (!vol_->readBlock(block, dst)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    else {
      uint8_t nb = toRead >> 9;
      if (type_ != FAT_FILE_TYPE_ROOT_FIXED) {
        uint8_t mb = vol_->blocksPerCluster() - blockOfCluster;
        if (mb < nb) nb = mb;
      }
      n = 512*nb;
      if (vol_->cacheBlockNumber() <= block
        && block < (vol_->cacheBlockNumber() + nb)) {
        // flush cache if a block is in the cache
        if (!vol_->cacheSync()) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
      }
      if (!vol_->sdCard()->readStart(block)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      for (uint8_t b = 0; b < nb; b++) {
        if (!vol_->sdCard()->readData(dst + b*512)) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
      }
      if (!vol_->sdCard()->readStop()) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    dst += n;
    curPosition_ += n;
    toRead -= n;
  }
  return nbyte;

FAIL:
  return -1;
}

/** 
 * Convert the dir_t name field of the file (which contains blank fills)
 * into a proper filename string without spaces inside.
 *
 * buffer MUST be at least a 13 char array!
 */
void SdBaseFile::createFilename(char* buffer, const dir_t &dirEntry) {
  const uint8_t* src = dirEntry.name;
  for (uint8_t i = 0; i < 11; i++, src++) {
    if (*src == ' ') continue; // ignore spaces
    if (i == 8) *buffer++ = '.';
    *buffer++ = *src;
  }
  *buffer = 0; // close the string
}

//------------------------------------------------------------------------------
/** Read the next directory entry from a directory file with the long filename
 *
 * \param[out] dir The dir_t struct that will receive the data.
 * \param[out] longFilename The long filename associated with the 8.3 name
 *
 * \return For success getLongFilename() returns a pointer to dir_t
 * A value of zero will be returned if end of file is reached.
 */
dir_t *SdBaseFile::getLongFilename(dir_t *dir, char *longFilename) {
  
  int16_t n;
  uint8_t bLastPart = true;
  uint8_t checksum  = 0;

  if (longFilename != NULL)
    *longFilename = 0;

  while (1) {
    //HAL::pingWatchdog();
    if (!(dir = readDirCache())) {
      return NULL;
    }

    if (dir->name[0] == DIR_NAME_FREE)
      return NULL;

    if (dir->name[0] == DIR_NAME_0XE5 || dir->name[0] == DIR_NAME_DELETED) {
      bLastPart = true;
      if (longFilename != NULL)
        *longFilename = 0;
      continue;
    }

    if (DIR_IS_LONG_NAME(dir)) {
     if (longFilename != NULL) {
        vfat_t *VFAT = (vfat_t*)dir;
        int8_t nSeq = VFAT->sequenceNumber & 0x1F;

        // Sanity check the VFAT entry. The first cluster is always set to zero. And the sequence number should be higher then 0
        if (VFAT->firstClusterLow == 0 && nSeq > 0 && nSeq <= MAX_VFAT_ENTRIES) {
          n = (nSeq - 1) * 13;

          longFilename[n + 0] = (char)VFAT->name1[0];
      		longFilename[n + 1] = (char)VFAT->name1[1];
      		longFilename[n + 2] = (char)VFAT->name1[2];
          longFilename[n + 3] = (char)VFAT->name1[3];
          longFilename[n + 4] = (char)VFAT->name1[4];
          longFilename[n + 5] = (char)VFAT->name2[0];
          longFilename[n + 6] = (char)VFAT->name2[1];
          longFilename[n + 7] = (char)VFAT->name2[2];
      		longFilename[n + 8] = (char)VFAT->name2[3];
      		longFilename[n + 9] = (char)VFAT->name2[4];
      		longFilename[n + 10] = (char)VFAT->name2[5];
      		longFilename[n + 11] = (char)VFAT->name3[0];
      		longFilename[n + 12] = (char)VFAT->name3[1];

          if (bLastPart) {
            checksum = VFAT->checksum;
            longFilename[n + 13] = 0;
          }
          bLastPart = false;
        }
      }
    }
    else {
      if (((dir->attributes & DIR_ATT_HIDDEN) || (dir->attributes & DIR_ATT_SYSTEM)) || (dir->name[0] == '.' && dir->name[1] != '.')) {
        bLastPart = true;
        if (longFilename != NULL)
          *longFilename = 0;
        continue;
      }
      if (DIR_IS_FILE(dir) || DIR_IS_SUBDIR(dir)) {
        if (longFilename && (bLastPart || checksum != lfn_checksum((unsigned char *)dir->name))) {
          createFilename(longFilename, *dir);
        }
        return dir;
      }
    }
  }
  return dir;
}

bool SdBaseFile::findSpace(dir_t *dir, int8_t cVFATNeeded, int8_t *pcVFATFound, uint32_t *pwIndexPos) {
  //int16_t n; // unused
  int8_t cVFATFound = 0;
  // if not a directory file or miss-positioned return an error
  if (!isDir()) return -1;

  rewind();

  while (1) {
    //HAL::pingWatchdog();
    dir = readDirCache();
    if (!dir) return false;
    // last entry if DIR_NAME_FREE
    if (dir->name[0] == DIR_NAME_FREE) return 0;
    // skip empty entries and entry for .  and ..
    if (dir->name[0] == DIR_NAME_0XE5 || dir->name[0] == DIR_NAME_DELETED) {
      if (DIR_IS_LONG_NAME(dir)) {
        //vfat_t *VFAT = (vfat_t*)dir; // unused
        cVFATFound++;
      }
      else {
        if (pwIndexPos != NULL && cVFATNeeded > 0 && cVFATFound >= cVFATNeeded && *pwIndexPos == 0) {
          *pwIndexPos = curPosition_-sizeof(dir_t)-(cVFATFound * sizeof(dir_t));
          *pcVFATFound = cVFATFound;
          return true;
        }
        cVFATFound++;
      }
    }
    else {
      cVFATFound = 0;
    }
  }
}

//------------------------------------------------------------------------------
/** Read the next directory entry from a directory file.
 *
 * \param[out] dir The dir_t struct that will receive the data.
 *
 * \return For success readDir() returns the number of bytes read.
 * A value of zero will be returned if end of file is reached.
 * If an error occurs, readDir() returns -1.  Possible errors include
 * readDir() called before a directory has been opened, this is not
 * a directory file or an I/O error occurred.
 */

int8_t SdBaseFile::readDir(dir_t* dir) {
  int16_t n;
  // if not a directory file or miss-positioned return an error
  if (!isDir() || (0x1F & curPosition_)) return -1;

  while (1) {
    n = read(dir, sizeof(dir_t));
    if (n != sizeof(dir_t)) return n == 0 ? 0 : -1;
    // last entry if DIR_NAME_FREE
    if (dir->name[0] == DIR_NAME_FREE) return 0;
    // skip empty entries and entry for .  and ..
    if (dir->name[0] == DIR_NAME_DELETED || dir->name[0] == '.') continue;
    // return if normal file or subdirectory
    if (DIR_IS_FILE_OR_SUBDIR(dir)) return n;
  }
}
//------------------------------------------------------------------------------
// Read next directory entry into the cache
// Assumes file is correctly positioned
dir_t* SdBaseFile::readDirCache() {
  uint8_t i;
  // error if not directory
  if (!isDir()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // index of entry in cache
  i = (curPosition_ >> 5) & 0xF;
  // use read to locate and cache block
  if (read() < 0) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // advance to next entry
  curPosition_ += 31;

  // return pointer to entry
  return vol_->cacheAddress()->dir + i;

FAIL:
  return 0;
}
//------------------------------------------------------------------------------
/** Remove a file.
 *
 * The directory entry and all data for the file are deleted.
 *
 * \note This function should not be used to delete the 8.3 version of a
 * file that has a long name. For example if a file has the long name
 * "New Text Document.txt" you should not delete the 8.3 name "NEWTEX~1.TXT".
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include the file read-only, is a directory,
 * or an I/O error occurred.
 */
bool SdBaseFile::remove() {
  dir_t* d;
  // free any clusters - will FAIL if read-only or directory
  if (!truncate(0)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // cache directory entry
  d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
  if (!d) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // mark entry deleted
  d->name[0] = DIR_NAME_DELETED;

  // set this file closed
  type_ = FAT_FILE_TYPE_CLOSED;

  // write entry to SD
  return vol_->cacheSync();
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Remove a file.
 *
 * The directory entry and all data for the file are deleted.
 *
 * \param[in] dirFile The directory that contains the file.
 * \param[in] path Path for the file to be removed.
 *
 * \note This function should not be used to delete the 8.3 version of a
 * file that has a long name. For example if a file has the long name
 * "New Text Document.txt" you should not delete the 8.3 name "NEWTEX~1.TXT".
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include the file is a directory, is read only,
 * \a dirFile is not a directory, \a path is not found
 * or an I/O error occurred.
 */
bool SdBaseFile::remove(SdBaseFile* dirFile, PGM_P path) {
  SdBaseFile file;
  if (!file.open(dirFile, path, O_WRITE)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  return file.remove();

 FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Rename a file or subdirectory.
 *
 * \param[in] dirFile Directory for the new path.
 * \param[in] newPath New path name for the file/directory.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include \a dirFile is not open or is not a directory
 * file, newPath is invalid or already exists, or an I/O error occurs.
 */
bool SdBaseFile::rename(SdBaseFile* dirFile, PGM_P newPath) {
  dir_t entry;
  uint32_t dirCluster = 0;
  SdBaseFile file;
  cache_t* pc;
  dir_t* d;

  // must be an open file or subdirectory
  if (!(isFile() || isSubDir())) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // can't move file
  if (vol_ != dirFile->vol_) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // sync() and cache directory entry
  sync();
  d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
  if (!d) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // save directory entry
  memcpy(&entry, d, sizeof(entry));

  // mark entry deleted
  d->name[0] = DIR_NAME_DELETED;

  // make directory entry for new path
  if (isFile()) {
    if (!file.open(dirFile, newPath, O_CREAT | O_EXCL | O_WRITE)) {
      goto restore;
    }
  }
  else {
    // don't create missing path prefix components
    if (!file.mkdir(dirFile, newPath, false)) {
      goto restore;
    }
    // save cluster containing new dot dot
    dirCluster = file.firstCluster_;
  }
  // change to new directory entry
  dirBlock_ = file.dirBlock_;
  dirIndex_ = file.dirIndex_;

  // mark closed to avoid possible destructor close call
  file.type_ = FAT_FILE_TYPE_CLOSED;

  // cache new directory entry
  d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
  if (!d) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // copy all but name field to new directory entry
  memcpy(&d->attributes, &entry.attributes, sizeof(entry) - sizeof(d->name));

  // update dot dot if directory
  if (dirCluster) {
    // get new dot dot
    uint32_t block = vol_->clusterStartBlock(dirCluster);
    pc = vol_->cacheFetch(block, SdVolume::CACHE_FOR_READ);
    if (!pc) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
   memcpy(&entry, &pc->dir[1], sizeof(entry));

    // free unused cluster
    if (!vol_->freeChain(dirCluster)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // store new dot dot
    block = vol_->clusterStartBlock(firstCluster_);
    pc = vol_->cacheFetch(block, SdVolume::CACHE_FOR_WRITE);
    if (!pc) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    memcpy(&pc->dir[1], &entry, sizeof(entry));
  }
  return vol_->cacheSync();

restore:
  d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
  if (!d) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // restore entry
  d->name[0] = entry.name[0];
  vol_->cacheSync();

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Remove a directory file.
 *
 * The directory file will be removed only if it is empty and is not the
 * root directory.  rmdir() follows DOS and Windows and ignores the
 * read-only attribute for the directory.
 *
 * \note This function should not be used to delete the 8.3 version of a
 * directory that has a long name. For example if a directory has the
 * long name "New folder" you should not delete the 8.3 name "NEWFOL~1".
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include the file is not a directory, is the root
 * directory, is not empty, or an I/O error occurred.
 */
bool SdBaseFile::rmdir() {
  // must be open subdirectory
  if (!isSubDir()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  rewind();

  // make sure directory is empty
  while (curPosition_ < fileSize_) {
    dir_t* p = readDirCache();
    if (!p) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // done if past last used entry
    if (p->name[0] == DIR_NAME_FREE) break;
    // skip empty slot, '.' or '..'
    if (p->name[0] == DIR_NAME_DELETED || p->name[0] == '.') continue;
    // error not empty
    if (DIR_IS_FILE_OR_SUBDIR(p)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  // convert empty directory to normal file for remove
  type_ = FAT_FILE_TYPE_NORMAL;
  flags_ |= O_WRITE;
  return remove();

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Recursively delete a directory and all contained files.
 *
 * This is like the Unix/Linux 'rm -rf *' if called with the root directory
 * hence the name.
 *
 * Warning - This will remove all contents of the directory including
 * subdirectories.  The directory will then be removed if it is not root.
 * The read-only attribute for files will be ignored.
 *
 * \note This function should not be used to delete the 8.3 version of
 * a directory that has a long name.  See remove() and rmdir().
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::rmRfStar() {
  uint32_t index;
  SdBaseFile f;
  rewind();
  while (curPosition_ < fileSize_) {
    // remember position
    index = curPosition_ / 32;

    dir_t* p = readDirCache();
    if (!p) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // done if past last entry
    if (p->name[0] == DIR_NAME_FREE) break;

    // skip empty slot or '.' or '..'
    if (p->name[0] == DIR_NAME_DELETED || p->name[0] == '.') continue;

    // skip if part of long file name or volume label in root
    if (!DIR_IS_FILE_OR_SUBDIR(p)) continue;

    if (!f.open(this, index, O_READ)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    if (f.isSubDir()) {
      // recursively delete
      if (!f.rmRfStar()) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    } else {
      // ignore read-only
      f.flags_ |= O_WRITE;
      if (!f.remove()) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    // position to next entry if required
    if (curPosition_ != (32UL*(index + 1))) {
      if (!seekSet(32UL*(index + 1))) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
  }
  // don't try to delete root
  if (!isRoot()) {
    if (!rmdir()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/**  Create a file object and open it in the current working directory.
 *
 * \param[in] path A path with a valid 8.3 DOS name for a file to be opened.
 *
 * \param[in] oflag Values for \a oflag are constructed by a bitwise-inclusive
 * OR of open flags. see SdBaseFile::open(SdBaseFile*, const char*, uint8_t).
 */
SdBaseFile::SdBaseFile(PGM_P path, uint8_t oflag) {
  type_ = FAT_FILE_TYPE_CLOSED;
  writeError = false;
  open(path, oflag);
}
//------------------------------------------------------------------------------
/** Sets a file's position.
 *
 * \param[in] pos The new position in bytes from the beginning of the file.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::seekSet(uint32_t pos) {
  uint32_t nCur;
  uint32_t nNew;
  // error if file not open or seek past end of file
  if (!isOpen() || pos > fileSize_) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (type_ == FAT_FILE_TYPE_ROOT_FIXED) {
    curPosition_ = pos;
    curCluster_ = 0;
    goto done;
  }
  if (pos == 0) {
    // set position to start of file
    curCluster_ = 0;
    curPosition_ = 0;
    goto done;
  }
  // calculate cluster index for cur and new position
  nCur = (curPosition_ - 1) >> (vol_->clusterSizeShift_ + 9);
  nNew = (pos - 1) >> (vol_->clusterSizeShift_ + 9);

  if (nNew < nCur || curPosition_ == 0) {
    // must follow chain from first cluster
    curCluster_ = firstCluster_;
  }
  else {
    // advance from curPosition
    nNew -= nCur;
  }
  while (nNew--) {
    if (!vol_->fatGet(curCluster_, &curCluster_)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  curPosition_ = pos;

done:
  return true;

FAIL:
  return false;
}
// set fileSize_ for a directory
bool SdBaseFile::setDirSize() {
  uint16_t s = 0;
  uint32_t cluster = firstCluster_;
  do {
    if (!vol_->fatGet(cluster, &cluster)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    s += vol_->blocksPerCluster();
    // max size if a directory file is 4096 blocks
    if (s >= 4096) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  } while (!vol_->isEOC(cluster));
  fileSize_ = 512L*s;
  return true;

FAIL:
  return false;
}

//-----------------------------------------------------------------------------
//------------------------------------------------------------------------------
void SdBaseFile::setpos(FatPos_t* pos) {
  curPosition_ = pos->position;
  curCluster_ = pos->cluster;
}
//------------------------------------------------------------------------------
/** The sync() call causes all modified data and directory fields
 * to be written to the storage device.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include a call to sync() before a file has been
 * opened or an I/O error.
 */
bool SdBaseFile::sync() {
  // only allow open files and directories
  if (!isOpen()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (flags_ & F_FILE_DIR_DIRTY) {
    dir_t* d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
    // check for deleted by another open file object
    if (!d || d->name[0] == DIR_NAME_DELETED) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // do not set filesize for dir files
    if (!isDir()) d->fileSize = fileSize_;

    // update first cluster fields
    d->firstClusterLow = firstCluster_ & 0xFFFF;
    d->firstClusterHigh = firstCluster_ >> 16;

    // set modify time if user supplied a callback date/time function
    if (dateTime_) {
      dateTime_(&d->lastWriteDate, &d->lastWriteTime);
      d->lastAccessDate = d->lastWriteDate;
    }
    // clear directory dirty
    flags_ &= ~F_FILE_DIR_DIRTY;
  }
  return vol_->cacheSync();

FAIL:
  writeError = true;
  return false;
}
//------------------------------------------------------------------------------
/** Copy a file's timestamps
 *
 * \param[in] file File to copy timestamps from.
 *
 * \note
 * Modify and access timestamps may be overwritten if a date time callback
 * function has been set by dateTimeCallback().
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::timestamp(SdBaseFile* file) {
  dir_t* d;
  dir_t dir;

  // get timestamps
  if (!file->dirEntry(&dir)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // update directory fields
  if (!sync()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
  if (!d) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // copy timestamps
  d->lastAccessDate = dir.lastAccessDate;
  d->creationDate = dir.creationDate;
  d->creationTime = dir.creationTime;
  d->creationTimeTenths = dir.creationTimeTenths;
  d->lastWriteDate = dir.lastWriteDate;
  d->lastWriteTime = dir.lastWriteTime;

  // write back entry
  return vol_->cacheSync();

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Set a file's timestamps in its directory entry.
 *
 * \param[in] flags Values for \a flags are constructed by a bitwise-inclusive
 * OR of flags from the following list
 *
 * T_ACCESS - Set the file's last access date.
 *
 * T_CREATE - Set the file's creation date and time.
 *
 * T_WRITE - Set the file's last write/modification date and time.
 *
 * \param[in] year Valid range 1980 - 2107 inclusive.
 *
 * \param[in] month Valid range 1 - 12 inclusive.
 *
 * \param[in] day Valid range 1 - 31 inclusive.
 *
 * \param[in] hour Valid range 0 - 23 inclusive.
 *
 * \param[in] minute Valid range 0 - 59 inclusive.
 *
 * \param[in] second Valid range 0 - 59 inclusive
 *
 * \note It is possible to set an invalid date since there is no check for
 * the number of days in a month.
 *
 * \note
 * Modify and access timestamps may be overwritten if a date time callback
 * function has been set by dateTimeCallback().
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool SdBaseFile::timestamp(uint8_t flags, uint16_t year, uint8_t month,
                           uint8_t day, uint8_t hour, uint8_t minute, uint8_t second) {
  uint16_t dirDate;
  uint16_t dirTime;
  dir_t* d;

  if (!isOpen()
    || year < 1980
    || year > 2107
    || month < 1
    || month > 12
    || day < 1
    || day > 31
    || hour > 23
    || minute > 59
    || second > 59) {
      DBG_FAIL_MACRO;
      goto FAIL;
  }
  // update directory entry
  if (!sync()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  d = cacheDirEntry(SdVolume::CACHE_FOR_WRITE);
  if (!d) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  dirDate = FAT_DATE(year, month, day);
  dirTime = FAT_TIME(hour, minute, second);
  if (flags & T_ACCESS) {
    d->lastAccessDate = dirDate;
  }
  if (flags & T_CREATE) {
    d->creationDate = dirDate;
    d->creationTime = dirTime;
    // seems to be units of 1/100 second not 1/10 as Microsoft states
    d->creationTimeTenths = second & 1 ? 100 : 0;
  }
  if (flags & T_WRITE) {
    d->lastWriteDate = dirDate;
    d->lastWriteTime = dirTime;
  }
  return vol_->cacheSync();

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Truncate a file to a specified length.  The current file position
 * will be maintained if it is less than or equal to \a length otherwise
 * it will be set to end of file.
 *
 * \param[in] length The desired length for the file.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 * Reasons for failure include file is read only, file is a directory,
 * \a length is greater than the current file size or an I/O error occurs.
 */
bool SdBaseFile::truncate(uint32_t length) {
  uint32_t newPos;
  // error if not a normal file or read-only
  if (!isFile() || !(flags_ & O_WRITE)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // error if length is greater than current size
  if (length > fileSize_) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // fileSize and length are zero - nothing to do
  if (fileSize_ == 0) return true;

  // remember position for seek after truncation
  newPos = curPosition_ > length ? length : curPosition_;

  // position to last cluster in truncated file
  if (!seekSet(length)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (length == 0) {
    // free all clusters
    if (!vol_->freeChain(firstCluster_)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    firstCluster_ = 0;
  } else {
    uint32_t toFree;
    if (!vol_->fatGet(curCluster_, &toFree)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    if (!vol_->isEOC(toFree)) {
      // free extra clusters
      if (!vol_->freeChain(toFree)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      // current cluster is end of chain
      if (!vol_->fatPutEOC(curCluster_)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
  }
  fileSize_ = length;

  // need to update directory entry
  flags_ |= F_FILE_DIR_DIRTY;

  if (!sync()) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // set file to correct position
  return seekSet(newPos);

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Write data to an open file.
 *
 * \note Data is moved to the cache but may not be written to the
 * storage device until sync() is called.
 *
 * \param[in] buf Pointer to the location of the data to be written.
 *
 * \param[in] nbyte Number of bytes to write.
 *
 * \return For success write() returns the number of bytes written, always
 * \a nbyte.  If an error occurs, write() returns -1.  Possible errors
 * include write() is called before a file has been opened, write is called
 * for a read-only file, device is full, a corrupt file system or an I/O error.
 *
 */
int SdBaseFile::write(const void* buf, size_t nbyte) {
  // convert void* to uint8_t*  -  must be before goto statements
  const uint8_t* src = reinterpret_cast<const uint8_t*>(buf);
    cache_t* pc;
    uint8_t cacheOption;
  // number of bytes left to write  -  must be before goto statements
  size_t nToWrite = nbyte;
  size_t n;

  // error if not a normal file or is read-only
  if (/*!isFile() || */!(flags_ & O_WRITE)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }

  // seek to end of file if append flag
  if ((flags_ & O_APPEND) && curPosition_ != fileSize_) {
    if (!seekEnd()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }

  while (nToWrite) {
    uint8_t blockOfCluster = vol_->blockOfCluster(curPosition_);
    uint16_t blockOffset = curPosition_ & 0x1FF;
    if (blockOfCluster == 0 && blockOffset == 0) {
      // start of new cluster
      if (curCluster_ != 0) {
        uint32_t next;
        if (!vol_->fatGet(curCluster_, &next)) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
        if (vol_->isEOC(next)) {
          // add cluster if at end of chain
          if (!addCluster()) {
            DBG_FAIL_MACRO;
            goto FAIL;
          }
        }
        else {
          curCluster_ = next;
        }
      } else {
        if (firstCluster_ == 0) {
          // allocate first cluster of file
          if (!addCluster()) {
            DBG_FAIL_MACRO;
            goto FAIL;
          }
        }
        else {
          curCluster_ = firstCluster_;
        }
      }
    }
    // block for data write
    uint32_t block = type_ == FAT_FILE_TYPE_ROOT_FIXED ? vol_->rootDirStart() + (curPosition_ >> 9) : vol_->clusterStartBlock(curCluster_) + blockOfCluster;

    if (blockOffset != 0 || nToWrite < 512) {
      // partial block - must use cache
      // max space in block
      n = 512 - blockOffset;
      // lesser of space and amount to write
      if (n > nToWrite) n = nToWrite;

      if (blockOffset == 0 && curPosition_ >= fileSize_) {
        // start of new block don't need to read into cache
        cacheOption = SdVolume::CACHE_RESERVE_FOR_WRITE;
      }
      else {
        // rewrite part of block
        cacheOption = SdVolume::CACHE_FOR_WRITE;
        }
        pc = vol_->cacheFetch(block, cacheOption);
        if (!pc) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
      uint8_t* dst = pc->data + blockOffset;
      memcpy(dst, src, n);
      if (512 == (n + blockOffset)) {
        if (!vol_->cacheWriteData()) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
      }
    } else if (!USE_MULTI_BLOCK_SD_IO || nToWrite < 1024) {
      // use single block write command
      n = 512;
      if (vol_->cacheBlockNumber() == block) {
        vol_->cacheInvalidate();
      }
      if (!vol_->writeBlock(block, src)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    else {
      // use multiple block write command
      uint8_t maxBlocks = vol_->blocksPerCluster() - blockOfCluster;
      uint8_t nBlock = nToWrite >> 9;
      if (nBlock > maxBlocks) nBlock = maxBlocks;

      n = 512*nBlock;
      if (!vol_->sdCard()->writeStart(block, nBlock)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      for (uint8_t b = 0; b < nBlock; b++) {
        // invalidate cache if block is in cache
        if ((block + b) == vol_->cacheBlockNumber()) {
          vol_->cacheInvalidate();
        }
        if (!vol_->sdCard()->writeData(src + 512*b)) {
          DBG_FAIL_MACRO;
          goto FAIL;
        }
      }
      if (!vol_->sdCard()->writeStop()) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    curPosition_ += n;
    src += n;
    nToWrite -= n;
  }
  if (curPosition_ > fileSize_) {
    // update fileSize and insure sync will update dir entry
    fileSize_ = curPosition_;
    flags_ |= F_FILE_DIR_DIRTY;
  }
  else if (dateTime_ && nbyte) {
    // insure sync will update modified date and time
    flags_ |= F_FILE_DIR_DIRTY;
  }

  if (flags_ & O_SYNC) {
    if (!sync()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  return nbyte;

FAIL:
  // return for write error
  writeError = true;
  return -1;
}
//------------------------------------------------------------------------------
// suppress cpplint warnings with NOLINT comment
#if ALLOW_DEPRECATED_FUNCTIONS && DISABLED(DOXYGEN)
void (*SdBaseFile::oldDateTime_)(uint16_t &date, uint16_t &time) = 0;  // NOLINT
#endif  // ALLOW_DEPRECATED_FUNCTIONS

// ============== Sd2Card.cpp =============

//==============================================================================
// debug trace macro
#define SD_TRACE(m, b)
// #define SD_TRACE(m, b) Serial.print(m);Serial.println(b);
//==============================================================================

/* Enable FAST CRC computations - You can trade speed for FLASH space if
 * needed by disabling the following define */
#define FAST_CRC 1

#if ENABLED(SD_CHECK_AND_RETRY)

  static bool crcSupported = true;

  #if ENABLED(FAST_CRC)

    static const uint8_t crctab7[] PROGMEM = {
      0x00,0x09,0x12,0x1B,0x24,0x2D,0x36,0x3F,0x48,0x41,0x5A,0x53,0x6C,0x65,0x7E,0x77,
      0x19,0x10,0x0B,0x02,0x3D,0x34,0x2F,0x26,0x51,0x58,0x43,0x4A,0x75,0x7C,0x67,0x6E,
      0x32,0x3B,0x20,0x29,0x16,0x1F,0x04,0x0D,0x7A,0x73,0x68,0x61,0x5E,0x57,0x4C,0x45,
      0x2B,0x22,0x39,0x30,0x0F,0x06,0x1D,0x14,0x63,0x6A,0x71,0x78,0x47,0x4E,0x55,0x5C,
      0x64,0x6D,0x76,0x7F,0x40,0x49,0x52,0x5B,0x2C,0x25,0x3E,0x37,0x08,0x01,0x1A,0x13,
      0x7D,0x74,0x6F,0x66,0x59,0x50,0x4B,0x42,0x35,0x3C,0x27,0x2E,0x11,0x18,0x03,0x0A,
      0x56,0x5F,0x44,0x4D,0x72,0x7B,0x60,0x69,0x1E,0x17,0x0C,0x05,0x3A,0x33,0x28,0x21,
      0x4F,0x46,0x5D,0x54,0x6B,0x62,0x79,0x70,0x07,0x0E,0x15,0x1C,0x23,0x2A,0x31,0x38,
      0x41,0x48,0x53,0x5A,0x65,0x6C,0x77,0x7E,0x09,0x00,0x1B,0x12,0x2D,0x24,0x3F,0x36,
      0x58,0x51,0x4A,0x43,0x7C,0x75,0x6E,0x67,0x10,0x19,0x02,0x0B,0x34,0x3D,0x26,0x2F,
      0x73,0x7A,0x61,0x68,0x57,0x5E,0x45,0x4C,0x3B,0x32,0x29,0x20,0x1F,0x16,0x0D,0x04,
      0x6A,0x63,0x78,0x71,0x4E,0x47,0x5C,0x55,0x22,0x2B,0x30,0x39,0x06,0x0F,0x14,0x1D,
      0x25,0x2C,0x37,0x3E,0x01,0x08,0x13,0x1A,0x6D,0x64,0x7F,0x76,0x49,0x40,0x5B,0x52,
      0x3C,0x35,0x2E,0x27,0x18,0x11,0x0A,0x03,0x74,0x7D,0x66,0x6F,0x50,0x59,0x42,0x4B,
      0x17,0x1E,0x05,0x0C,0x33,0x3A,0x21,0x28,0x5F,0x56,0x4D,0x44,0x7B,0x72,0x69,0x60,
      0x0E,0x07,0x1C,0x15,0x2A,0x23,0x38,0x31,0x46,0x4F,0x54,0x5D,0x62,0x6B,0x70,0x79
    };

    static uint8_t CRC7(const uint8_t* data, uint8_t n) {
      uint8_t crc = 0;
      while ( n > 0 ) {
        crc = pgm_read_byte(&crctab7[ (crc << 1) ^ *data++ ]);
        n--;
      }
      return (crc << 1) | 1;
    }

  #else // DISABLED(FAST_CRC)

    static uint8_t CRC7(const uint8_t* data, uint8_t n) {
      uint8_t crc = 0;
      for (uint8_t i = 0; i < n; i++) {
        uint8_t d = data[i];
        d ^= crc << 1;
        if (d & 0x80) d ^= 9;
        crc = d ^ (crc & 0x78) ^ (crc << 4) ^ ((crc >> 3) & 15);
        crc &= 0x7F;
      }
      crc = (crc << 1) ^ (crc << 4) ^ (crc & 0x70) ^ ((crc >> 3) & 0x0F);
      return crc | 1;
    }

  #endif // // DISABLED(FAST_CRC)

#endif // ENABLED(SD_CHECK_AND_RETRY)

//==============================================================================
// Sd2Card member functions
//------------------------------------------------------------------------------
// send command and return error code.  Return zero for OK
uint8_t Sd2Card::cardCommand(const uint8_t cmd, uint32_t arg) {
  // select card
  chipSelect();

  // wait up to 300 ms if busy
  waitNotBusy(SD_WRITE_TIMEOUT);

  uint8_t *pa = reinterpret_cast<uint8_t *>(&arg);

#if ENABLED(SD_CHECK_AND_RETRY)

  // form message
  uint8_t d[6] = {(uint8_t) (cmd | 0x40), pa[3], pa[2], pa[1], pa[0] };

  // add crc
  d[5] = CRC7(d, 5);

  // send message
  for (uint8_t k = 0; k < 6; k++ )
    HAL::spiSend(d[k]);

#else

  // send command
  HAL::spiSend(cmd | 0x40);

  // send argument
  for (int8_t i = 3; i >= 0; i--)
    HAL::spiSend(pa[i]);

  // send CRC - correct for CMD0 with arg zero or CMD8 with arg 0x1AA
  HAL::spiSend(cmd == CMD0 ? 0x95 : 0x87);

#endif  // SD_CHECK_AND_RETRY

  // additional delay for CMD0
  if (cmd == CMD0) HAL::delayMilliseconds(100);

  // skip stuff byte for stop read
  if (cmd == CMD12) HAL::spiReceive();

  // wait for response
  for (uint8_t i = 0; ((status_ = HAL::spiReceive()) & 0x80) && i != 0xFF; i++);
  return status_;
}

/**
 * Determine the size of an SD flash memory card.
 *
 * \return The number of 512 byte data blocks in the card
 *         or zero if an error occurs.
 */
uint32_t Sd2Card::cardSize() {
  csd_t csd;
  if (!readCSD(&csd)) return 0;
  if (csd.v1.csd_ver == 0) {
    uint8_t read_bl_len = csd.v1.read_bl_len;
    uint16_t c_size = (csd.v1.c_size_high << 10)
                      | (csd.v1.c_size_mid << 2) | csd.v1.c_size_low;
    uint8_t c_size_mult = (csd.v1.c_size_mult_high << 1)
                          | csd.v1.c_size_mult_low;
    return (uint32_t)(c_size + 1) << (c_size_mult + read_bl_len - 7);
  }
  else if (csd.v2.csd_ver == 1) {
    uint32_t c_size = ((uint32_t)csd.v2.c_size_high << 16)
                      | (csd.v2.c_size_mid << 8) | csd.v2.c_size_low;
    return (c_size + 1) << 10;
  }
  else {
    error(SD_CARD_ERROR_BAD_CSD);
    return 0;
  }
}

void Sd2Card::chipDeselect() {
  HAL::digitalWrite(chipSelectPin_, HIGH);
  // insure MISO goes high impedance
  HAL::spiSend(0xFF);
}
//------------------------------------------------------------------------------
void Sd2Card::chipSelect() {
  HAL::spiInit(spiRate_);
  HAL::digitalWrite(chipSelectPin_, LOW);
}

/** Erase a range of blocks.
 *
 * \param[in] firstBlock The address of the first block in the range.
 * \param[in] lastBlock The address of the last block in the range.
 *
 * \note This function requests the SD card to do a flash erase for a
 * range of blocks.  The data on the card after an erase operation is
 * either 0 or 1, depends on the card vendor.  The card must support
 * single block erase.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool Sd2Card::erase(uint32_t firstBlock, uint32_t lastBlock) {
  csd_t csd;
  if (!readCSD(&csd)) goto FAIL;
  // check for single block erase
  if (!csd.v1.erase_blk_en) {
    // erase size mask
    uint8_t m = (csd.v1.sector_size_high << 1) | csd.v1.sector_size_low;
    if ((firstBlock & m) != 0 || ((lastBlock + 1) & m) != 0) {
      // error card can't erase specified area
      error(SD_CARD_ERROR_ERASE_SINGLE_BLOCK);
      goto FAIL;
    }
  }
  if (type_ != SD_CARD_TYPE_SDHC) {
    firstBlock <<= 9;
    lastBlock <<= 9;
  }
  if (cardCommand(CMD32, firstBlock)
      || cardCommand(CMD33, lastBlock)
      || cardCommand(CMD38, 0)) {
    error(SD_CARD_ERROR_ERASE);
    goto FAIL;
  }
  if (!waitNotBusy(SD_ERASE_TIMEOUT)) {
    error(SD_CARD_ERROR_ERASE_TIMEOUT);
    goto FAIL;
  }
  chipDeselect();
  return true;

FAIL:
  chipDeselect();
  return false;
}

/** Determine if card supports single block erase.
 *
 * \return The value one, true, is returned if single block erase is supported.
 * The value zero, false, is returned if single block erase is not supported.
 */
bool Sd2Card::eraseSingleBlockEnable() {
  csd_t csd;
  return readCSD(&csd) ? csd.v1.erase_blk_en : false;
}

/**
 * Initialize an SD flash memory card.
 *
 * \param[in] sckRateID SPI clock rate selector. See setSckRate().
 * \param[in] chipSelectPin SD chip select pin number.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.  The reason for failure
 * can be determined by calling errorCode() and errorData().
 */
bool Sd2Card::init(uint8_t sckRateID, uint8_t chipSelectPin) {
  errorCode_ = type_ = 0;
  chipSelectPin_ = chipSelectPin;
  // 16-bit init start time allows over a minute
  uint16_t t0 = (uint16_t)millis();
  uint32_t arg;

  // If init takes more than 4s it could trigger
  // watchdog leading to a reboot loop.
  watchdog.reset();

  pinMode(chipSelectPin_, OUTPUT);
  digitalWrite(chipSelectPin_, HIGH);
  HAL::spiBegin();

  // set SCK rate for initialization commands
  spiRate_ = SPI_SD_INIT_RATE;
  HAL::spiInit(spiRate_);

  // must supply min of 74 clock cycles with CS high.
  for (uint8_t i = 0; i < 20; i++) HAL::spiSend(0xFF);

  // command to go idle in SPI mode
  while (cardCommand(CMD0, 0) != R1_IDLE_STATE) {
    if (((uint16_t)millis() - t0) > SD_INIT_TIMEOUT) {
      error(SD_CARD_ERROR_CMD0);
      goto FAIL;
    }
  }

  #if ENABLED(SD_CHECK_AND_RETRY)
    crcSupported = (cardCommand(CMD59, 1) == R1_IDLE_STATE);
  #endif

  // check SD version
  for (;;) {
    if (cardCommand(CMD8, 0x1AA) == (R1_ILLEGAL_COMMAND | R1_IDLE_STATE)) {
      type(SD_CARD_TYPE_SD1);
      break;
    }

    for (uint8_t i = 0; i < 4; i++) status_ = HAL::spiReceive();
    if (status_ == 0xAA) {
      type(SD_CARD_TYPE_SD2);
      break;
    }

    if (((uint16_t)millis() - t0) > SD_INIT_TIMEOUT) {
      error(SD_CARD_ERROR_CMD8);
      goto FAIL;
    }
  }

  // initialize card and send host supports SDHC if SD2
  arg = type() == SD_CARD_TYPE_SD2 ? 0x40000000 : 0;
  while ((status_ = cardAcmd(ACMD41, arg)) != R1_READY_STATE) {
    // check for timeout
    if (((uint16_t)millis() - t0) > SD_INIT_TIMEOUT) {
      error(SD_CARD_ERROR_ACMD41);
      goto FAIL;
    }
  }
  // if SD2 read OCR register to check for SDHC card
  if (type() == SD_CARD_TYPE_SD2) {
    if (cardCommand(CMD58, 0)) {
      error(SD_CARD_ERROR_CMD58);
      goto FAIL;
    }
    if ((HAL::spiReceive() & 0xC0) == 0xC0) type(SD_CARD_TYPE_SDHC);
    // discard rest of ocr - contains allowed voltage range
    for (uint8_t i = 0; i < 3; i++) HAL::spiReceive();
  }
  chipDeselect();
  return setSckRate(sckRateID);

FAIL:
  chipDeselect();
  return false;
}

/**
 * Read a 512 byte block from an SD card.
 *
 * \param[in] blockNumber Logical block to be read.
 * \param[out] dst Pointer to the location that will receive the data.
 * \return The value one, true, is returned for success and
 */
bool Sd2Card::readBlock(uint32_t blockNumber, uint8_t* dst) {

  // use address if not SDHC card
  if (type()!= SD_CARD_TYPE_SDHC) blockNumber <<= 9;

  #if ENABLED(SD_CHECK_AND_RETRY)
    uint8_t retryCnt = 3;
    for(;;) {
      if (cardCommand(CMD17, blockNumber))
        error(SD_CARD_ERROR_CMD17);
      else if (readData(dst, 512))
        return true;

      chipDeselect();
      if (!--retryCnt) break;

      cardCommand(CMD12, 0); // Try sending a stop command, ignore the result.
      errorCode_ = 0;
    }
    return false;
  #else
    if (cardCommand(CMD17, blockNumber)) {
      error(SD_CARD_ERROR_CMD17);
      chipDeselect();
      return false;
    }
    else
      return readData(dst, 512);
  #endif
}

/** Read one data block in a multiple block read sequence
 *
 * \param[in] dst Pointer to the location for the data to be read.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool Sd2Card::readData(uint8_t* dst) {
  chipSelect();
  return readData(dst, 512);
}

#if ENABLED(SD_CHECK_AND_RETRY)

  #if ENABLED(FAST_CRC)
    static const uint16_t crctab16[] PROGMEM = {
      0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
      0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
      0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
      0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
      0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
      0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
      0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
      0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
      0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
      0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
      0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
      0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
      0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
      0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
      0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
      0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
      0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
      0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
      0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
      0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
      0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
      0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
      0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
      0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
      0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
      0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
      0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
      0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
      0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
      0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
      0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
      0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
    };
      // faster CRC-CCITT
      // uses the x^16,x^12,x^5,x^1 polynomial.
    static uint16_t CRC_CCITT(const uint8_t* data, size_t n) {
      uint16_t crc = 0;
      for (size_t i = 0; i < n; i++) {
        crc = pgm_read_word(&crctab16[(crc >> 8 ^ data[i]) & 0xFF]) ^ (crc << 8);
      }
      return crc;
    }
  #else
    // slower CRC-CCITT
    // uses the x^16,x^12,x^5,x^1 polynomial.
    static uint16_t CRC_CCITT(const uint8_t* data, size_t n) {
      uint16_t crc = 0;
      for (size_t i = 0; i < n; i++) {
        crc = (uint8_t)(crc >> 8) | (crc << 8);
        crc ^= data[i];
        crc ^= (uint8_t)(crc & 0xFF) >> 4;
        crc ^= crc << 12;
        crc ^= (crc & 0xFF) << 5;
      }
      return crc;
    }
  #endif
#endif // SD_CHECK_AND_RETRY

bool Sd2Card::readData(uint8_t* dst, size_t count) {
  // wait for start block token
  uint16_t t0 = millis();
  while ((status_ = HAL::spiReceive()) == 0xFF) {
    if (((uint16_t)millis() - t0) > SD_READ_TIMEOUT) {
      error(SD_CARD_ERROR_READ_TIMEOUT);
      goto FAIL;
    }
  }
  if (status_ != DATA_START_BLOCK) {
    error(SD_CARD_ERROR_READ);
    goto FAIL;
  }
  // transfer data
  HAL::spiReadBlock(dst, count);

  #if ENABLED(SD_CHECK_AND_RETRY)
    {
      uint16_t recvCrc = (HAL::spiReceive() << 8) | HAL::spiReceive();
      if (crcSupported && recvCrc != CRC_CCITT(dst, count)) {
        error(SD_CARD_ERROR_READ_CRC);
        goto FAIL;
      }
    }
  #else
    // discard CRC
    HAL::spiReceive();
    HAL::spiReceive();
  #endif

  chipDeselect();
  return true;

FAIL:
  chipDeselect();
  return false;
}

/** read CID or CSR register */
bool Sd2Card::readRegister(uint8_t cmd, void* buf) {
  uint8_t* dst = reinterpret_cast<uint8_t*>(buf);
  if (cardCommand(cmd, 0)) {
    error(SD_CARD_ERROR_READ_REG);
    chipDeselect();
    return false;
  }
  return readData(dst, 16);
}

/** Start a read multiple blocks sequence.
 *
 * \param[in] blockNumber Address of first block in sequence.
 *
 * \note This function is used with readData() and readStop() for optimized
 * multiple block reads.  SPI chipSelect must be low for the entire sequence.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool Sd2Card::readStart(uint32_t blockNumber) {
  if (type() != SD_CARD_TYPE_SDHC) blockNumber <<= 9;
  if (cardCommand(CMD18, blockNumber)) {
    error(SD_CARD_ERROR_CMD18);
    chipDeselect();
    return false;
  }
  chipDeselect();
  return true;
}

/** End a read multiple blocks sequence.
 *
* \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool Sd2Card::readStop() {
  chipSelect();
  if (cardCommand(CMD12, 0)) {
    error(SD_CARD_ERROR_CMD12);
    chipDeselect();
    return false;
  }
  chipDeselect();
  return true;
}

/**
 * Set the SPI clock rate.
 *
 * \param[in] sckRateID A value in the range [0, 14].
 *
 * The SPI clock divisor will be set to approximately
 *
 * (2 + (sckRateID & 1)) << ( sckRateID/2)
 *
 * The maximum SPI rate is F_CPU/2 for \a sckRateID = 0 and the rate is
 * F_CPU/128 for \a scsRateID = 12.
 *
 * \return The value one, true, is returned for success and the value zero,
 * false, is returned for an invalid value of \a sckRateID.
 */
bool Sd2Card::setSckRate(uint8_t sckRateID) {
  if (sckRateID > MAX_SCK_RATE_ID) {
    error(SD_CARD_ERROR_SCK_RATE);
    return false;
  }
  spiRate_ = sckRateID;
  return true;
}

// wait for card to go not busy
bool Sd2Card::waitNotBusy(uint32_t timeoutMillis) {
  uint32_t t0 = millis();
  while (HAL::spiReceive() != 0xFF) {
    if (((uint32_t)millis() - t0) >= timeoutMillis) return false;
  }
  return true;
}

/**
 * Writes a 512 byte block to an SD card.
 *
 * \param[in] blockNumber Logical block to be written.
 * \param[in] src Pointer to the location of the data to be written.
 * \return The value one, true, is returned for success and
 */
bool Sd2Card::writeBlock(uint32_t blockNumber, const uint8_t* src) {
  // use address if not SDHC card
  if (type() != SD_CARD_TYPE_SDHC) blockNumber <<= 9;
  if (cardCommand(CMD24, blockNumber)) {
    error(SD_CARD_ERROR_CMD24);
    goto FAIL;
  }
  if (!writeData(DATA_START_BLOCK, src)) goto FAIL;

  // wait for flash programming to complete
  if (!waitNotBusy(SD_WRITE_TIMEOUT)) {
    error(SD_CARD_ERROR_WRITE_TIMEOUT);
    goto FAIL;
  }
  // response is r2 so get and check two bytes for nonzero
  if (cardCommand(CMD13, 0) || HAL::spiReceive()) {
    error(SD_CARD_ERROR_WRITE_PROGRAMMING);
    goto FAIL;
  }
  chipDeselect();
  return true;

FAIL:
  chipDeselect();
  return false;
}

/** Write one data block in a multiple block write sequence
 * \param[in] src Pointer to the location of the data to be written.
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.
 */
bool Sd2Card::writeData(const uint8_t* src) {
  chipSelect();
  // wait for previous write to finish
  if (!waitNotBusy(SD_WRITE_TIMEOUT) || !writeData(WRITE_MULTIPLE_TOKEN, src)) {
    error(SD_CARD_ERROR_WRITE_MULTIPLE);
    chipDeselect();
    return false;
  }
  chipDeselect();
  return true;
}

// send one block of data for write block or write multiple blocks
bool Sd2Card::writeData(uint8_t token, const uint8_t* src) {

  #if ENABLED(SD_CHECK_AND_RETRY)
    uint16_t crc = CRC_CCITT(src, 512);
  #else  // SD_CHECK_AND_RETRY
    uint16_t crc = 0xFFFF;
  #endif  // SD_CHECK_AND_RETRY

  HAL::spiSendBlock(token, src);
  HAL::spiSend(crc >> 8);
  HAL::spiSend(crc & 0xFF);

  status_ = HAL::spiReceive();
  if ((status_ & DATA_RES_MASK) != DATA_RES_ACCEPTED) {
    error(SD_CARD_ERROR_WRITE);
    chipDeselect();
    return false;
  }
  return true;
}

/** Start a write multiple blocks sequence.
 *
 * \param[in] blockNumber Address of first block in sequence.
 * \param[in] eraseCount The number of blocks to be pre-erased.
 *
 * \note This function is used with writeData() and writeStop()
 * for optimized multiple block writes.
 *
 * \return The value one, true, is returned for success and
 */
bool Sd2Card::writeStart(uint32_t blockNumber, uint32_t eraseCount) {
  // send pre-erase count
  if (cardAcmd(ACMD23, eraseCount)) {
    error(SD_CARD_ERROR_ACMD23);
    goto FAIL;
  }
  // use address if not SDHC card
  if (type() != SD_CARD_TYPE_SDHC) blockNumber <<= 9;
  if (cardCommand(CMD25, blockNumber)) {
    error(SD_CARD_ERROR_CMD25);
    goto FAIL;
  }
  chipDeselect();
  return true;
  FAIL:
  chipDeselect();
  return false;
}

/** End a write multiple blocks sequence.
 *
 * \return The value one, true, is returned for success and
 */
bool Sd2Card::writeStop() {
  chipSelect();
  if (!waitNotBusy(SD_WRITE_TIMEOUT)) goto FAIL;
  HAL::spiSend(STOP_TRAN_TOKEN);
  if (!waitNotBusy(SD_WRITE_TIMEOUT)) goto FAIL;
  chipDeselect();
  return true;

FAIL:
  error(SD_CARD_ERROR_STOP_TRAN);
  chipDeselect();
  return false;
}

// =================== SdVolume ===================

//------------------------------------------------------------------------------
#if !USE_MULTIPLE_CARDS
// raw block cache

cache_t  SdVolume::cacheBuffer_;       // 512 byte cache for Sd2Card
uint32_t SdVolume::cacheBlockNumber_;  // current block number
uint8_t  SdVolume::cacheStatus_;       // status of cache block
uint32_t SdVolume::cacheFatOffset_;    // offset for mirrored FAT
#if USE_SEPARATE_FAT_CACHE
cache_t  SdVolume::cacheFatBuffer_;       // 512 byte cache for FAT
uint32_t SdVolume::cacheFatBlockNumber_;  // current Fat block number
uint8_t  SdVolume::cacheFatStatus_;       // status of cache Fatblock
#endif  // USE_SEPARATE_FAT_CACHE
Sd2Card* SdVolume::sdCard_;            // pointer to SD card object
#endif  // USE_MULTIPLE_CARDS
//------------------------------------------------------------------------------
// find a contiguous group of clusters
bool SdVolume::allocContiguous(uint32_t count, uint32_t* curCluster) {
  // start of group
  uint32_t bgnCluster;
  // end of group
  uint32_t endCluster;
  // last cluster of FAT
  uint32_t fatEnd = clusterCount_ + 1;

  // flag to save place to start next search
  bool setStart;

  // set search start cluster
  if (*curCluster) {
    // try to make file contiguous
    bgnCluster = *curCluster + 1;

    // don't save new start location
    setStart = false;
  }
  else {
    // start at likely place for free cluster
    bgnCluster = allocSearchStart_;

    // save next search start if one cluster
    setStart = count == 1;
  }
  // end of group
  endCluster = bgnCluster;

  // search the FAT for free clusters
  for (uint32_t n = 0;; n++, endCluster++) {
    // can't find space checked all clusters
    if (n >= clusterCount_) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }

    // past end - start from beginning of FAT
    if (endCluster > fatEnd) {
      bgnCluster = endCluster = 2;
    }
    uint32_t f;
    if (!fatGet(endCluster, &f)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }

    if (f != 0) {
      // cluster in use try next cluster as bgnCluster
      bgnCluster = endCluster + 1;
    }
    else if ((endCluster - bgnCluster + 1) == count) {
      // done - found space
      break;
    }
  }
  // mark end of chain
  if (!fatPutEOC(endCluster)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }

  // link clusters
  while (endCluster > bgnCluster) {
    if (!fatPut(endCluster - 1, endCluster)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    endCluster--;
  }
  if (*curCluster != 0) {
    // connect chains
    if (!fatPut(*curCluster, bgnCluster)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  // return first cluster number to caller
  *curCluster = bgnCluster;
  // remember possible next free cluster
  if (setStart) allocSearchStart_ = bgnCluster + 1;
  return true;

FAIL:
  return false;
}
//==============================================================================

// cache functions

#if USE_SEPARATE_FAT_CACHE

//------------------------------------------------------------------------------
cache_t* SdVolume::cacheFetch(uint32_t blockNumber, uint8_t options) {
  return cacheFetchData(blockNumber, options);
}
//------------------------------------------------------------------------------
cache_t* SdVolume::cacheFetchData(uint32_t blockNumber, uint8_t options) {
  if (cacheBlockNumber_ != blockNumber) {
    if (!cacheWriteData()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    if (!(options & CACHE_OPTION_NO_READ)) {
      if (!sdCard_->readBlock(blockNumber, cacheBuffer_.data)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    cacheStatus_ = 0;
    cacheBlockNumber_ = blockNumber;
  }
  cacheStatus_ |= options & CACHE_STATUS_MASK;
  return &cacheBuffer_;

FAIL:
  return 0;
}
//------------------------------------------------------------------------------
cache_t* SdVolume::cacheFetchFat(uint32_t blockNumber, uint8_t options) {
  if (cacheFatBlockNumber_ != blockNumber) {
    if (!cacheWriteFat()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    if (!(options & CACHE_OPTION_NO_READ)) {
      if (!sdCard_->readBlock(blockNumber, cacheFatBuffer_.data)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    cacheFatStatus_ = 0;
    cacheFatBlockNumber_ = blockNumber;
  }
  cacheFatStatus_ |= options & CACHE_STATUS_MASK;
  return &cacheFatBuffer_;

FAIL:
  return 0;
}
//------------------------------------------------------------------------------
bool SdVolume::cacheSync() {
  return cacheWriteData() && cacheWriteFat();
}
//------------------------------------------------------------------------------
bool SdVolume::cacheWriteData() {
  if (cacheStatus_ & CACHE_STATUS_DIRTY) {
    if (!sdCard_->writeBlock(cacheBlockNumber_, cacheBuffer_.data)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    cacheStatus_ &= ~CACHE_STATUS_DIRTY;
  }
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
bool SdVolume::cacheWriteFat() {
  if (cacheFatStatus_ & CACHE_STATUS_DIRTY) {
    if (!sdCard_->writeBlock(cacheFatBlockNumber_, cacheFatBuffer_.data)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // mirror second FAT
    if (cacheFatOffset_) {
      uint32_t lbn = cacheFatBlockNumber_ + cacheFatOffset_;
      if (!sdCard_->writeBlock(lbn, cacheFatBuffer_.data)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    cacheFatStatus_ &= ~CACHE_STATUS_DIRTY;
  }
  return true;

FAIL:
  return false;
}
#else  // USE_SEPARATE_FAT_CACHE
//------------------------------------------------------------------------------
cache_t* SdVolume::cacheFetch(uint32_t blockNumber, uint8_t options) {
  if (cacheBlockNumber_ != blockNumber) {
    if (!cacheSync()) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    if (!(options & CACHE_OPTION_NO_READ)) {
      if (!sdCard_->readBlock(blockNumber, cacheBuffer_.data)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    cacheStatus_ = 0;
    cacheBlockNumber_ = blockNumber;
  }
  cacheStatus_ |= options & CACHE_STATUS_MASK;
  return &cacheBuffer_;

 FAIL:
  return 0;
}
//------------------------------------------------------------------------------
cache_t* SdVolume::cacheFetchFat(uint32_t blockNumber, uint8_t options) {
  return cacheFetch(blockNumber, options | CACHE_STATUS_FAT_BLOCK);
}
//------------------------------------------------------------------------------
bool SdVolume::cacheSync() {
  if (cacheStatus_ & CACHE_STATUS_DIRTY) {
#ifdef GLENN_DEBUG
    SERIAL_EMT("Wr blk:", cacheBlockNumber_);
#endif
    if (!sdCard_->writeBlock(cacheBlockNumber_, cacheBuffer_.data)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // mirror second FAT
    if ((cacheStatus_ & CACHE_STATUS_FAT_BLOCK) && cacheFatOffset_) {
      uint32_t lbn = cacheBlockNumber_ + cacheFatOffset_;
      if (!sdCard_->writeBlock(lbn, cacheBuffer_.data)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    cacheStatus_ &= ~CACHE_STATUS_DIRTY;
  }
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
bool SdVolume::cacheWriteData() {
  return cacheSync();
}
#endif  // USE_SEPARATE_FAT_CACHE
//------------------------------------------------------------------------------
void SdVolume::cacheInvalidate() {
    cacheBlockNumber_ = 0xFFFFFFFF;
    cacheStatus_ = 0;
}
//==============================================================================
//------------------------------------------------------------------------------
uint32_t SdVolume::clusterStartBlock(uint32_t cluster) const {
  return dataStartBlock_ + ((cluster - 2)*blocksPerCluster_);
}
//------------------------------------------------------------------------------
// Fetch a FAT entry
bool SdVolume::fatGet(uint32_t cluster, uint32_t* value) {
  uint32_t lba;
  cache_t* pc;

  // error if reserved cluster of beyond FAT

  if (cluster < 2  || cluster > (clusterCount_ + 1)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }

  if (FAT12_SUPPORT && fatType_ == 12) {
    uint16_t index = cluster;
    index += index >> 1;
    lba = fatStartBlock_ + (index >> 9);
    pc = cacheFetchFat(lba, CACHE_FOR_READ);
    if (!pc) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    index &= 0x1FF;
    uint16_t tmp = pc->data[index];
    index++;
    if (index == 512) {
      pc = cacheFetchFat(lba + 1, CACHE_FOR_READ);
      if (!pc) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      index = 0;
    }
    tmp |= pc->data[index] << 8;
    *value = cluster & 1 ? tmp >> 4 : tmp & 0xFFF;
    return true;
  }
  if (fatType_ == 16) {
    lba = fatStartBlock_ + (cluster >> 8);
  }
  else if (fatType_ == 32) {
    lba = fatStartBlock_ + (cluster >> 7);
  }
  else {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  pc = cacheFetchFat(lba, CACHE_FOR_READ);
  if (!pc) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (fatType_ == 16) {
    *value = pc->fat16[cluster & 0xFF];
  }
  else {
    *value = pc->fat32[cluster & 0x7F] & FAT32MASK;
  }
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
// Store a FAT entry
bool SdVolume::fatPut(uint32_t cluster, uint32_t value) {
  uint32_t lba;
  cache_t* pc;
  // error if reserved cluster of beyond FAT
  if (cluster < 2 || cluster > (clusterCount_ + 1)) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  if (FAT12_SUPPORT && fatType_ == 12) {
    uint16_t index = cluster;
    index += index >> 1;
    lba = fatStartBlock_ + (index >> 9);
    pc = cacheFetchFat(lba, CACHE_FOR_WRITE);
    if (!pc) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    index &= 0x1FF;
    uint8_t tmp = value;
    if (cluster & 1) {
      tmp = (pc->data[index] & 0xF) | tmp << 4;
    }
    pc->data[index] = tmp;

    index++;
    if (index == 512) {
      lba++;
      index = 0;
      pc = cacheFetchFat(lba, CACHE_FOR_WRITE);
      if (!pc) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
    }
    tmp = value >> 4;
    if (!(cluster & 1)) {
      tmp = ((pc->data[index] & 0xF0)) | tmp >> 4;
    }
    pc->data[index] = tmp;
    return true;
  }
  if (fatType_ == 16) {
    lba = fatStartBlock_ + (cluster >> 8);
  }
  else if (fatType_ == 32) {
    lba = fatStartBlock_ + (cluster >> 7);
  }
  else {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  pc = cacheFetchFat(lba, CACHE_FOR_WRITE);
  if (!pc) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  // store entry
  if (fatType_ == 16) {
    pc->fat16[cluster & 0xFF] = value;
  }
  else {
    pc->fat32[cluster & 0x7F] = value;
  }
  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
// free a cluster chain
bool SdVolume::freeChain(uint32_t cluster) {
  uint32_t next;

  // clear free cluster location
  allocSearchStart_ = 2;

  do {
    if (!fatGet(cluster, &next)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    // free cluster
    if (!fatPut(cluster, 0)) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }

    cluster = next;
  } while (!isEOC(cluster));

  return true;

FAIL:
  return false;
}
//------------------------------------------------------------------------------
/** Volume free space in clusters.
 *
 * \return Count of free clusters for success or -1 if an error occurs.
 */
int32_t SdVolume::freeClusterCount() {
  uint32_t free = 0;
  uint32_t lba;
  uint32_t todo = clusterCount_ + 2;
  uint16_t n;

  if (FAT12_SUPPORT && fatType_ == 12) {
    for (unsigned i = 2; i < todo; i++) {
      uint32_t c;
      if (!fatGet(i, &c)) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      if (c == 0) free++;
    }
  }
  else if (fatType_ == 16 || fatType_ == 32) {
    lba = fatStartBlock_;
    while (todo) {
      cache_t* pc = cacheFetchFat(lba++, CACHE_FOR_READ);
      if (!pc) {
        DBG_FAIL_MACRO;
        goto FAIL;
      }
      n = fatType_ == 16 ? 256 : 128;
      if (todo < n) n = todo;
      if (fatType_ == 16) {
        for (uint16_t i = 0; i < n; i++) {
          if (pc->fat16[i] == 0) free++;
        }
      }
      else {
        for (uint16_t i = 0; i < n; i++) {
          if (pc->fat32[i] == 0) free++;
        }
      }
      todo -= n;
    }
  }
  else {
    // invalid FAT type
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  return free;

 FAIL:
  return -1;
}
//------------------------------------------------------------------------------
/** Initialize a FAT volume.
 *
 * \param[in] dev The SD card where the volume is located.
 *
 * \param[in] part The partition to be used.  Legal values for \a part are
 * 1-4 to use the corresponding partition on a device formatted with
 * a MBR, Master Boot Record, or zero if the device is formatted as
 * a super floppy with the FAT boot sector in block zero.
 *
 * \return The value one, true, is returned for success and
 * the value zero, false, is returned for failure.  Reasons for
 * failure include not finding a valid partition, not finding a valid
 * FAT file system in the specified partition or an I/O error.
 */
bool SdVolume::init(Sd2Card* dev, uint8_t part) {
  uint32_t totalBlocks;
  uint32_t volumeStartBlock = 0;
  fat32_boot_t* fbs;
  cache_t* pc;
  sdCard_ = dev;
  fatType_ = 0;
  allocSearchStart_ = 2;
  cacheStatus_ = 0;  // cacheSync() will write block if true
  cacheBlockNumber_ = 0xFFFFFFFF;
  cacheFatOffset_ = 0;
  #if ENABLED(USE_SERARATEFAT_CACHE) && USE_SERARATEFAT_CACHE
    cacheFatStatus_ = 0;  // cacheSync() will write block if true
    cacheFatBlockNumber_ = 0xFFFFFFFF;
  #endif  // USE_SERARATEFAT_CACHE
  // if part == 0 assume super floppy with FAT boot sector in block zero
  // if part > 0 assume mbr volume with partition table
  if (part) {
    if (part > 4) {
#if ENABLED(DEBUG_SD_ERROR)
	SERIAL_LM(ER, "volume init: illegal part");
#endif		
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    pc = cacheFetch(volumeStartBlock, CACHE_FOR_READ);
    if (!pc) {
#if ENABLED(DEBUG_SD_ERROR)
		SERIAL_LM(ER, "volume init: cache fetch failed");
#endif
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    part_t* p = &pc->mbr.part[part-1];
    if ((p->boot & 0x7F) !=0  ||
      p->totalSectors < 100 ||
      p->firstSector == 0) {
      // not a valid partition
      DBG_FAIL_MACRO;
      goto FAIL;
    }
    volumeStartBlock = p->firstSector;
  }
  pc = cacheFetch(volumeStartBlock, CACHE_FOR_READ);
  if (!pc) {
    DBG_FAIL_MACRO;
    goto FAIL;
  }
  fbs = &(pc->fbs32);
  if (fbs->bytesPerSector != 512 ||
    fbs->fatCount == 0 ||
    fbs->reservedSectorCount == 0 ||
    fbs->sectorsPerCluster == 0) {
      // not valid FAT volume
      DBG_FAIL_MACRO;
      goto FAIL;
  }
  fatCount_ = fbs->fatCount;
  blocksPerCluster_ = fbs->sectorsPerCluster;
  // determine shift that is same as multiply by blocksPerCluster_
  clusterSizeShift_ = 0;
  while (blocksPerCluster_ != (1 << clusterSizeShift_)) {
    // error if not power of 2
    if (clusterSizeShift_++ > 7) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  blocksPerFat_ = fbs->sectorsPerFat16 ? fbs->sectorsPerFat16 : fbs->sectorsPerFat32;

  if (fatCount_ > 0) cacheFatOffset_ = blocksPerFat_;
  fatStartBlock_ = volumeStartBlock + fbs->reservedSectorCount;

  // count for FAT16 zero for FAT32
  rootDirEntryCount_ = fbs->rootDirEntryCount;

  // directory start for FAT16 dataStart for FAT32
  rootDirStart_ = fatStartBlock_ + fbs->fatCount * blocksPerFat_;

  // data start for FAT16 and FAT32
  dataStartBlock_ = rootDirStart_ + ((32 * fbs->rootDirEntryCount + 511) / 512);

  // total blocks for FAT16 or FAT32
  totalBlocks = fbs->totalSectors16 ? fbs->totalSectors16 : fbs->totalSectors32;

  // total data blocks
  clusterCount_ = totalBlocks - (dataStartBlock_ - volumeStartBlock);

  // divide by cluster size to get cluster count
  clusterCount_ >>= clusterSizeShift_;

  // FAT type is determined by cluster count
  if (clusterCount_ < 4085) {
    fatType_ = 12;
    if (!FAT12_SUPPORT) {
      DBG_FAIL_MACRO;
      goto FAIL;
    }
  }
  else if (clusterCount_ < 65525) {
    fatType_ = 16;
  }
  else {
    rootDirStart_ = fbs->fat32RootCluster;
    fatType_ = 32;
  }
  return true;

FAIL:
  return false;
}
// =============== SdFile.cpp ====================

/**  Create a file object and open it in the current working directory.
 *
 * \param[in] path A path with a valid 8.3 DOS name for a file to be opened.
 *
 * \param[in] oflag Values for \a oflag are constructed by a bitwise-inclusive
 * OR of open flags. see SdBaseFile::open(SdBaseFile*, const char*, uint8_t).
 */
SdFile::SdFile(PGM_P path, uint8_t oflag) : SdBaseFile(path, oflag) {
}
//------------------------------------------------------------------------------
/** Write data to an open file.
 *
 * \note Data is moved to the cache but may not be written to the
 * storage device until sync() is called.
 *
 * \param[in] buf Pointer to the location of the data to be written.
 *
 * \param[in] nbyte Number of bytes to write.
 *
 * \return For success write() returns the number of bytes written, always
 * \a nbyte.  If an error occurs, write() returns -1.  Possible errors
 * include write() is called before a file has been opened, write is called
 * for a read-only file, device is full, a corrupt file system or an I/O error.
 *
 */
int SdFile::write(const void* buf, size_t nbyte) {
  return SdBaseFile::write(buf, nbyte);
}
//------------------------------------------------------------------------------
/** Write a byte to a file. Required by the Arduino Print class.
 * \param[in] b the byte to be written.
 * Use getWriteError to check for errors.
 * \return 1 for success and 0 for failure.
 */
#if ENABLED(CPU_32_BIT)
  #ifdef COMPAT_PRE1
    void SdFile::write(uint8_t b) {
      dBaseFile::write(&b, 1);
    }
  #else
    size_t SdFile::write(uint8_t b) {
      return SdBaseFile::write(&b, 1) == 1 ? 1 : 0;
    }
  #endif

  //------------------------------------------------------------------------------
  /** Write a string to a file. Used by the Arduino Print class.
   * \param[in] str Pointer to the string.
   * Use getWriteError to check for errors.
   * \return count of characters written for success or -1 for failure.
   */
  int SdFile::write(PGM_P str) {
    return SdBaseFile::write(str, strlen(str));
  }
#else
  #if ARDUINO >= 100
    size_t SdFile::write(uint8_t b) {
      return SdBaseFile::write(&b, 1);
    }
  #else
    void SdFile::write(uint8_t b) {
      SdBaseFile::write(&b, 1);
    }
  #endif
  //------------------------------------------------------------------------------
  /** Write a string to a file. Used by the Arduino Print class.
   * \param[in] str Pointer to the string.
   * Use writeError to check for errors.
   */
  void SdFile::write(PGM_P str) {
    SdBaseFile::write(str, strlen(str));
  }
#endif

//------------------------------------------------------------------------------
/** Write a PROGMEM string to a file.
 * \param[in] str Pointer to the PROGMEM string.
 * Use writeError to check for errors.
 */
void SdFile::write_P(PGM_P str) {
  for (uint8_t c; (c = pgm_read_byte(str)); str++) write(c);
}
//------------------------------------------------------------------------------
/** Write a PROGMEM string followed by CR/LF to a file.
 * \param[in] str Pointer to the PROGMEM string.
 * Use writeError to check for errors.
 */
void SdFile::writeln_P(PGM_P str) {
  write_P(str);
  write_P(PSTR("\r\n"));
}

// ================ SdFatUtil.cpp ===================

//------------------------------------------------------------------------------
/** %Print a string in flash memory to Serial.
 *
 * \param[in] str Pointer to string stored in flash memory.
 */
void SdFatUtil::SerialPrint_P(PGM_P str) {
  SERIAL_TXT(str);
}
//------------------------------------------------------------------------------
/** %Print a string in flash memory to Serial followed by a CR/LF.
 *
 * \param[in] str Pointer to string stored in flash memory.
 */
void SdFatUtil::SerialPrintln_P(PGM_P str) {
  SERIAL_ET(str);
}

// ==============

#endif  // SDSUPPORT
